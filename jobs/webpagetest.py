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


"""Quinico Webpagetest Data Processor

   Requirements:
    - A properly configured Quinico environment (database, logging, configuration params)

"""


import os
import logging
import urllib
import json
import datetime
import pytz
import quinico
import Queue
import threading
import time
import traceback
import xml.etree.ElementTree as ET
from optparse import OptionParser
from django.conf import settings
from qclasses import qemail
from qclasses import qsql
from qclasses import qlib


# -- GLOBALLY AVAILABLE -- #

# Max wait between status checks
wpt_wait = ''

# Max attempts per test
wpt_attempts = ''

# Downloaded report path
report_path = ''

# API key
wpt_key = ''

# Grab the Quinico webapp settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'quinico.settings'

# Setup an instance of the Quinico logger
logger = logging.getLogger('quinico')

# Parse Arguments
parser = OptionParser(description='Web Page Test query \
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
                t_location = row[3]
        
                logger.info('Found a test: id:%s, domain:%s, url:%s, location:%s' % (t_id,t_domain,t_url,t_location))
                query_webpagetest(qs,qm,ql,t_id,t_domain,t_url,t_location)

                # Let the queue know I am done
                self.queue.task_done()

            except Queue.Empty:
                # Queue is empty, close down this thread.
                logger.info('Queue is empty, stopping thread %s' % t_name)

                # Disconnect from the DB server
                qs.close()

                # Stop the thread
                break

            except Exception:
                # Most likely there was a problem with the Webpagetest API
                # This generally should not happen as the function definitions that
                # that perform the work have their own exception handling
                logger.error('Exception encountered with thread %s: %s' % (t_name,traceback.format_exc()))
                if settings.SMTP_NOTIFY_ERROR:
                    qm.send('Error','Exception encountered with thread %s: %s' % (t_name,traceback.format_exc()))

                # Disconnect from the DB server
                qs.close()

                # Stop the thread
                break


def obtain_tests(qs,qm):
    """
    Obtain a list of tests
    """

    logger.info('Looking for webpagetests')

    # Create SQL statement
    sql = """
           SELECT webpagetest_test.id,domain,url,location
           FROM webpagetest_test
           INNER JOIN webpagetest_domain on webpagetest_test.domain_id=webpagetest_domain.id
           INNER JOIN webpagetest_url on webpagetest_test.url_id=webpagetest_url.id
           INNER JOIN webpagetest_location on webpagetest_test.location_id=webpagetest_location.id"""

    (rowcount,rows) = qs.execute(sql)
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    # return the data
    return rows


def query_webpagetest(qs,qm,ql,t_id,domain,u,l):
    """
    Query the Webpagetest API
    """

    logger.info('Checking %s for url %s from location %s' % (domain,u,l))

    test_url = 'http://www.webpagetest.org/runtest.php?f=json&runs=1&%s'
    stat_url = 'http://www.webpagetest.org/testStatus.php?test=%s&f=json'

    params = {}
    params['url'] = '%s%s' % (domain,u)
    params['location'] = l

    url = test_url % urllib.urlencode(params) 

    # Can't url_encode the key
    url += '&k=%s' % wpt_key

    response = ql.http_request1('webpagetest',url,1)
    if not response:
        return

    logger.debug(json.dumps(response))
    raw_json = json.loads(response)

    # We are interested in the statusCode, testId, xmlUrl and jsonUrl
    submit_status_code = raw_json['statusCode']
    logger.info('submit status code: %s' % submit_status_code)

    # Sometimes the JSON returned from WPT is incomplete.  In this case, unfortunately,
    # we have to bail
    try:
        testId = raw_json['data']['testId']
        logger.info('test id: %s' % testId)

        json_url = raw_json['data']['jsonUrl']
        logger.info('json url: %s' % json_url)

        xml_url = raw_json['data']['xmlUrl']
        logger.info('xml url: %s' % xml_url)
    except Exception as e:
        logger.error('Error encountered in parsing json: domain:%s,error:%s,raw_data:%s' % (domain,e,raw_json))
        ql.add_api_calls('webpagetest',1,1)
        if settings.SMTP_NOTIFY_ERROR:
            qm.send('Error','Error encountered in parsing json:\ndomain:%s\nerror:%s\nraw_data:%s' % (domain,e,raw_json))
        return

    # We'll check at periodic intervals to see if the test has completed and we'll check a maximum
    # number of times and then give up
    status_url = stat_url % testId 
    test_status_code = ''
    counter = 0
    while test_status_code != 200:
        if counter != 0:
           logger.info('Counter is at %s with a maximum of %s periods.  Sleeping %s seconds.' % (counter,wpt_attempts,wpt_wait))
           ql.pause(int(wpt_wait))
        
        test_status_code = check_status(ql,status_url)
        counter += 1

        # Could not obtain a status so quit checking
        if counter >= int(wpt_attempts):
            logger.error('Could not obtain WPT status for %s within %s intervals' % (status_url,wpt_attempts))
            if settings.SMTP_NOTIFY_ERROR:
                qm.send('Error','Could not obtain WPT status for %s within %s intervals' % (status_url,wpt_attempts))
            return

    # We received a good status (the test is done)
    # Now grab the data (these API calls are not counted against our total)
    logger.info('downloading report from %s' % xml_url)
    x_response = ql.http_request1('webpagetest',xml_url,None)
    if not x_response:
        logger.error('Could not obtain WPT test results for %s from %s.' % (domain,xml_url))
        if settings.SMTP_NOTIFY_ERROR:
            qm.send('Error','Could not obtain WPT test results for %s from %s.' % (domain,xml_url))
        return

    xml = ET.fromstring(x_response)

    # Save the full report
    report_file = ql.save_report(report_path,'webpagetest',x_response)

    # Create a datetime object for right now
    time_now = datetime.datetime.now()

    # Add the server's timezone and then convert to UTC before adding to the DB
    time_now = ql.convert_date_utc(time_now,settings.TIME_ZONE)

    # List of metrics we are tracking
    output_values = ['loadTime','TTFB','bytesOut','bytesOutDoc','bytesIn','bytesInDoc','connections','requests','requestsDoc','responses_200','responses_404','responses_other','result','render','fullyLoaded','cached','docTime','domTime','score_cache','score_cdn','score_gzip','score_cookies','score_keep-alive','score_minify','score_combine','score_compress','score_etags','gzip_total','gzip_savings','minify_total','minify_savings','image_total','image_savings','aft','domElements']

    # We are doing only one run with a repeat view
    # If one view fails, then the whole test will be marked as failed
    # We need to figure this out before looking at each test status as
    # we are inserting data into the DB after analyzing each run
    test_failed = 0
    try:
        successful_runs_fv = xml.findall('./data/successful%sRuns' % ('FV'))[0].text
        successful_runs_rv = xml.findall('./data/successful%sRuns' % ('RV'))[0].text

        if not successful_runs_fv == '1' or not successful_runs_rv == '1':
            test_failed = 1
    except Exception as e:
        test_failed = 1

    # Look through each view for specific data
    for view in [1,2]:

        if view == 1:
           view_num = 'firstView'
           view_type = 'FV'
        elif view == 2:
           view_num = 'repeatView'
           view_type = 'RV'

        values = []

        # Add the values we know about
        values.append(time_now)
        values.append(t_id)
        values.append(testId)
        values.append(view)

        # Run through the values we are looking for from WPT
        # If there is no value, insert a zero
        for output_value in output_values:
            try:
                values.append(xml.findall('./data/run/%s/results/%s' % (view_num,output_value))[0].text)
            except Exception as e:
                # The value was not there, so add a zero
                values.append(0)
                logger.warning('Error encountered searching for %s in view %s for %s:nError: %s,Url: %s' % (output_value,view,domain,e,xml_url))

        # Add the view status (we should have one successful run for FV and RV)
        # Start with success
        view_failed = 0

        try:
            successful_runs = xml.findall('./data/successful%sRuns' % (view_type))[0].text
            logger.debug('Successful %s runs:%s' % (view_type,successful_runs))

            if not successful_runs == '1':
                view_failed = 1

        except Exception as e:
            logger.warning('Error encountered searching %s runs for %s : %s : %s.' % (view_type,domain,xml_url,e))
            view_failed = 1
        
        # Add the view and test status
        values.append(view_failed)
        values.append(test_failed)

        # Add the report file (it will be the same report file for both views)
        values.append(report_file)

        sql = """
           INSERT INTO webpagetest_score (date,test_id,testId,viewNumber,loadTime,ttfb,bytesOut,bytesOutDoc,bytesIn,bytesInDoc,connections,requests,requestsDoc,responses_200,responses_404,responses_other,result,render,fullyLoaded,cached,docTime,domTime,score_cache,score_cdn,score_gzip,score_cookies,score_keep_alive,score_minify,score_combine,score_compress,score_etags,gzip_total,gzip_savings,minify_total,minify_savings,image_total,image_savings,aft,domElements,view_failed,test_failed,report)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        if not options.test:
            qs.execute(sql,values)
            if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
                qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def check_status(ql,url):
    """
    Check test status
    """

    logger.info('Checking test results')

    # These API calls are not counted against our total
    response = ql.http_request1('webpagetest',url,None)
    if not response:
        return

    logger.debug(json.dumps(response))
    raw_json = json.loads(response)

    # We are interested in the statusCode only
    test_status_code = raw_json['statusCode']
    logger.info('test status code: %s' % test_status_code)

    return test_status_code


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
    """Main Program Execution"""

    # Create qm, qs and ql instances so we can do some work
    (qm,qs,ql) = create_resources()

    # If we could not connect to MySQL, quit and notify someone
    if qs.status != 0:
        ql.terminate()

    # Send a test message, if requested to do so and then quit
    if options.message:
        qm.send('Webpagetest Test','Test message from the Quinico Webpagetest data collection job')

        # Disconnect from the DB server and exit
        qs.close()
        exit(0)

    # Check if another instance is already running
    if ql.check_pid('%s/jobs/pid/webpagetest.pid' % settings.APP_DIR):
        ql.terminate()

    # Set a PID
    if (ql.set_pid('%s/jobs/pid/webpagetest.pid' % settings.APP_DIR)):
        ql.terminate()

    # Let someone know we are starting data collection
    logger.info('Started Webpagetest data collection job')
    smtp_notify_data_start = int(ql.return_config('smtp_notify_data_start'))
    if smtp_notify_data_start:
        qm.send('Webpagetest Job Starting','Starting Quinico Webpagetest data collection job')

    # Obtain configuration parameters
    # If we cannot obtain any of these, we have to quit

    # Web Page Test key
    global wpt_key
    wpt_key = ql.return_config('wpt_key')
    if wpt_key is None:
        logger.error('wpt_key is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('wpt_key = *****')

    # Downloaded Report Path
    global report_path
    report_path = ql.return_config('report_path')
    if report_path is None:
        logger.error('Report path location is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('Report path location = %s' % report_path)

    # Max attempts per test
    global wpt_attempts
    wpt_attempts = ql.return_config('wpt_attempts')
    if wpt_attempts is None:
        logger.error('wpt_attempts is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('wpt_attempts = %s' % wpt_attempts)

    # Max wait between status checks
    global wpt_wait
    wpt_wait = ql.return_config('wpt_wait')
    if wpt_wait is None:
        logger.error('wpt_wait is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('wpt_wait = %s' % wpt_wait)

    wpt_threads = ql.return_config('wpt_threads')
    if wpt_threads is None:
        logger.error('Webpagetest threads is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('Webpagetest threads = %s' % wpt_threads)

    # Check all domains and urls
    tests = obtain_tests(qs,qm)
    if not tests:
        logger.error('No webpagetests defined')
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
        for i in range(int(wpt_threads)):
            # Create a worker and pass it the queue
            w = Worker(queue)

            # Start the worker
            w.start()

        # If all threads except this one are done, then quit
        # Check at 1 second intervals
        while threading.active_count() > 1:
            time.sleep(1)


    # All done
    logger.info('All done with webpagetest data processing')

    # Disconnect from the DB server
    qs.close()

    # Remove the PID file
    if (ql.remove_pid('%s/jobs/pid/webpagetest.pid' % settings.APP_DIR)):
        ql.terminate()


# This program can only run is executed directly
if __name__ == "__main__":

    # Run main program
    main()

    # Quit program
    exit(0)

