#!/usr/bin/python

#
# Copyright 2012 - Tom Alessi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Quinico Google Pagespeed Data Processor

   Requirements:
    - A properly configured Quinico environment (database, logging, configuration params)

"""

import os
import logging
import quinico
import urllib
import json
import uuid
import datetime
import Queue
import threading
import time
from optparse import OptionParser
from django.conf import settings
from qclasses import qemail
from qclasses import qsql
from qclasses import qlib


# -- GLOBALLY AVAILABLE -- #

# Google API key
google_key = ''

# The Pagespeed locale
pagespeed_locale = ''

# The path to save reports
report_path = ''

# Grab the Quinico webapp settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'quinico.settings'

# Setup an instance of the Quinico logger
# Logging is thread-safe so all threads will share the same logger
logger = logging.getLogger('quinico')

# Parse Arguments
parser = OptionParser(description='Google Pagespeed query \
and data loading script', version='%prog 1.0')
parser.add_option('-m','--message',
                  action='store_true',
                  dest='message',
                  default=False,
                  help='Send a test email message using the Quinico SMTP settings \
                        configured in local_settings.py and then exit')
parser.add_option('-t','--test',
                  action='store_true',
                  dest='test',
                  default=False,
                  help='Enable testing mode to prevent modification \
                        of any database data when this script is run.  \
                        No data will be added or deleted from the database \
                        except for API calls/errors.')
(options, args) = parser.parse_args()

# -- END GLOBALLY AVAILABLE -- #


class Worker(threading.Thread):
    """Worker thread for talking to external API 
    and acquiring/committing data

    To avoid contention, each thread will have its own ql, qs and
    qemail instance
    """

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        t_name = threading.current_thread().name
        logger.info('Starting thread: %s' % t_name)

        # Create qm, qs and ql instances
        (qm,qs,ql) = create_resources()

        while True:
            # Pop the next job off the queue and don't block if empty
            try:
                row = self.queue.get(False)
                t_id = row[0]
                t_domain = row[1]
                t_url = row[2]

                logger.info('%s found a test: id:%s, domain:%s, url:%s' % (t_name,t_id,t_domain,t_url))

                query_pagespeed(qs,qm,ql,t_id,t_domain,t_url,'desktop')
                query_pagespeed(qs,qm,ql,t_id,t_domain,t_url,'mobile')

                # Let the queue know I am done
                self.queue.task_done()

            except Queue.Empty:
                # Queue is empty, close down this thread.
                logger.info('Queue is empty, stopping thread %s' % t_name)

                # Disconnect from the DB server
                qs.close()

                # Stop the thread
                break

            except Exception as e:
                # Most likely there was a problem with the Pagespeed API
                # This generally should not happen as the function definitions that
                # that perform the work have their own exception handling
                logger.error('Exception encountered with thread %s: %s' % (t_name,e))
                if settings.SMTP_NOTIFY_ERROR:
                    qm.send('Error','Exception encountered with thread %s: %s' % (t_name,e))

                # Disconnect from the DB server
                qs.close()

                # Stop the thread
                break


def obtain_tests(qs,qm):
    """
    Obtain a list of tests
    """

    logger.info('Looking for domains')

    # Create SQL statement
    sql = """
           SELECT pagespeed_test.id,domain,url
           FROM pagespeed_test
           INNER JOIN pagespeed_domain on pagespeed_test.domain_id=pagespeed_domain.id
           INNER JOIN pagespeed_url on pagespeed_test.url_id=pagespeed_url.id"""

    (rowcount,rows) = qs.execute(sql)
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    # return the data
    return rows


def query_pagespeed(qs,qm,ql,t_id,domain,u,strategy):
    """
    Query the Google Pagespeed API
    """

    logger.info('Checking %s for url %s with strategy %s' % (domain,u,strategy))

    base_url = 'https://www.googleapis.com/pagespeedonline/v1/runPagespeed?%s'

    params = {}
    params['url'] = 'http://%s%s' % (domain,u)
    params['strategy'] = strategy
    params['locale'] = pagespeed_locale

    url = base_url % urllib.urlencode(params) 

    # Can't url_encode the google key
    url += '&key=%s' % google_key

    # Create a datetime object for right now
    time_now = datetime.datetime.now()

    # Add the server's timezone and then convert to UTC before adding to the DB
    time_now = ql.convert_date_utc(time_now,settings.TIME_ZONE)

    response = ql.http_request1('pagespeed',url,1)
    if not response:
        return

    logger.debug(json.dumps(response))
    raw_json = json.loads(response)

    # Add the high level scores that we save for every test
    # We are looking for the following items, in this order:
    items = [
        'numberHosts',
        'numberResources',
        'numberCssResources',
        'numberStaticResources',
        'totalRequestBytes',
        'textResponseBytes',
        'cssResponseBytes',
        'htmlResponseBytes',
        'imageResponseBytes',
        'javascriptResponseBytes',
        'otherResponseBytes'
        ]

    # Store the results
    results = []

    # Add the first few items
    results.append(time_now)
    results.append(t_id)
    results.append(strategy)
    results.append(raw_json['score'])
    
    # Add the rest of the items
    for item in items:
        if item in raw_json['pageStats']:
            results.append(raw_json['pageStats'][item])
        else:
            results.append(0) 

    # Add the full report
    report_file = ql.save_report(report_path,'pagespeed',json.dumps(raw_json))
    results.append(report_file)

    sql = """
           INSERT INTO pagespeed_score (
                                        date,
                                        test_id,
                                        strategy,
                                        score,
                                        numberHosts,
                                        numberResources,
                                        numberCssResources,
                                        numberStaticResources,
                                        totalRequestBytes,
                                        textResponseBytes,
                                        cssResponseBytes,
                                        htmlResponseBytes,
                                        imageResponseBytes,
                                        javascriptResponseBytes,
                                        otherResponseBytes,
                                        report
                                       )
           VALUES (
           %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    if not options.test:
        qs.execute(sql,results)
        if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
            qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def create_resources():
    """Create and return the following resources
       - a qlib instance
       - a qemail instance
       - a qsql instance
    """
       
    # Obtain database parameters from DJango
    host = settings.DATABASES['default']['HOST']
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    name = settings.DATABASES['default']['NAME']

    # Create a qemail instance
    qm = qemail.notify(settings.SMTP_HOST,
                      settings.SMTP_SENDER,
                      settings.SMTP_RECIPIENT,
                      logger
                     )

    # Create a qsql instance
    qs = qsql.sql(host,user,password,name,logger)

    # Create a qlib instance
    ql = qlib.lib(qs,qm,settings.SMTP_NOTIFY_ERROR,logger)

    return (qm,qs,ql)


def main():
    """ Main Program Execution"""

    # Create qm, qs and ql instances so we can do some work
    (qm,qs,ql) = create_resources()

    # If we could not connect to MySQL, quit and notify someone
    if qs.status != 0:
        ql.terminate()

    # Send a test message, if requested to do so and then quit
    if options.message:
        qm.send('Pagespeed Test','Test message from the Quinico Pagespeed data collection job')

        # Disconnect from the DB server and exit
        qs.close()
        exit(0)

    # Check if another instance is already running
    if ql.check_pid('%s/jobs/pid/pagespeed.pid' % settings.APP_DIR):
        ql.terminate()

    # Set a PID
    if (ql.set_pid('%s/jobs/pid/pagespeed.pid' % settings.APP_DIR)):
        ql.terminate()

    # Let someone know we are starting data collection
    logger.info('Started Pagespeed data collection job')
    smtp_notify_data_start = int(ql.return_config('smtp_notify_data_start'))
    if smtp_notify_data_start:
        qm.send('Pagespeed Job Starting','Starting Quinico Pagespeed data collection job')

    # Obtain configuration parameters
    # If we cannot obtain any of these, we have to quit
    
    # Google key
    global google_key
    google_key = ql.return_config('google_key')
    if google_key is None:
        logger.error('Google Key is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('Google Key = %s' % google_key)

    # Downloaded Report Path
    global report_path
    report_path = ql.return_config('report_path')
    if report_path is None:
        logger.error('Report path location is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('Report path location = %s' % report_path)

    # Pagespeed Locale
    global pagespeed_locale
    pagespeed_locale = ql.return_config('pagespeed_locale')
    if pagespeed_locale is None:
        logger.error('Google Pagespeed locale is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('Google Pagespeed locale = %s' % pagespeed_locale)

    # Pagespeed Threads
    pagespeed_threads = ql.return_config('pagespeed_threads')
    if pagespeed_threads is None:
        logger.error('Google Pagespeed threads is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('Google Pagespeed threads = %s' % pagespeed_threads)

    # Check all domains and urls
    tests = obtain_tests(qs,qm)
    if not tests:
        logger.error('No pagespeed tests defined')
        ql.terminate()
    else:
        # Create a queue for the tests
        queue = Queue.Queue()

        # Add all tests to the queue 
        for row in tests:
            queue.put(row)

        # Start the workers.  
        #   Notes:
        #   - Keep the main thread open until it is the only one left
        #   - Do not daemonize the threads nor join on the queue
        #   - If the threads experience exceptions, or if they detect
        #     that the queue is empty, they will die.
        #   - The above prevents the threads dieing due to exceptions w/ the API
        #     and the queue never emptying.   It is preferable to have this process 
        #     die and someone get alerted and investigate.
        for i in range(int(pagespeed_threads)):
            # Create a worker and pass it the queue
            w = Worker(queue)

            # Start the worker
            w.start()

        # If all threads except this one are done, then quit
        # Check at 1 second intervals
        while threading.active_count() > 1: 
            time.sleep(1)


    # All done
    logger.info('All done with pagespeed data processing')

    # Disconnect from the DB server
    qs.close()

    # Remove the PID file
    if (ql.remove_pid('%s/jobs/pid/pagespeed.pid' % settings.APP_DIR)):
        ql.terminate()


# This program can only run is executed directly
if __name__ == "__main__":

    # Run main program
    main()

    # Quit program
    exit(0)

