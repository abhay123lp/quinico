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
from optparse import OptionParser
from django.conf import settings
from qclasses import qemail
from qclasses import qsql
from qclasses import qlib



def obtain_tests():
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


def query_pagespeed(t_id,domain,u,strategy):
    """
    Query the Google Pagespeed API
    """

    logger.info('Checking %s for url %s with strategy %s' % (domain,u,strategy))

    base_url = 'https://www.googleapis.com/pagespeedonline/v1/runPagespeed?%s'

    params = {}
    params['url'] = 'http://%s%s' % (domain,u)
    params['strategy'] = strategy

    url = base_url % urllib.urlencode(params) 

    # Can't url_encode the google key
    url += '&key=%s' % google_key

    response = ql.http_request1('pagespeed',url,1)
    if not response:
        return

    logger.debug(json.dumps(response))
    raw_json = json.loads(response)

    ## Add the high level scores that we save for every test ##
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

    # Keep the results here
    results = []

    # Add the first few items
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

    # Directory name
    date_path = datetime.datetime.now().strftime('%Y/%m/%d')

    # Unique filename
    file_name = uuid.uuid4()
    
    # Save the report to disk
    # Do everything at once to make error handling easier
    try:
        # Create the date directory if its not already there
        if not os.path.exists('%s/%s' % (pagespeed_upload,date_path)):
            os.makedirs('%s/%s' % (pagespeed_upload,date_path))

        # Save the file
        report_file = open('%s/%s/%s' % (pagespeed_upload,date_path,file_name),'w')
        report_file.write(json.dumps(raw_json))
        report_file.close()
      
        # Save the file name for the DB
        results.append('%s/%s' % (date_path,file_name))
    except Exception as e:
        logger.error('Error saving report file for %s: %s' % (domain,e))
        if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
            qm.send('Error','Error saving report file for %s: %s' % (domain,e))

        # Save nothing to the DB
        results.append('')

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
           VALUES (DATE(NOW()),
           %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    if not options.test:
        qs.execute(sql,results)
        if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
            qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))



#
# BEGIN MAIN PROGRAM EXECUTION
#


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

# Grab the Quinico webapp settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'quinico.settings'

# Setup an instance of the Quinico logger
logger = logging.getLogger('quinico')

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

# Send a test message, if requested to do so and then quit
if options.message:
    qm.send('Pagespeed Test','Test message from the Quinico Pagespeed data collection job')
    exit(0)

# Create a qsql instance
qs = qsql.sql(host,user,password,name,logger)

# Create a qlib instance
ql = qlib.lib(qs,qm,settings.SMTP_NOTIFY_ERROR,logger)

# If we could not connect to MySQL, quit and notify someone
if qs.status != 0:
    ql.terminate()

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
google_key = ql.return_config('google_key')
if google_key is None:
    logger.error('Google Key is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('Google Key = %s' % google_key)

pagespeed_upload = ql.return_config('pagespeed_upload')
if pagespeed_upload is None:
    logger.error('Google Pagespeed upload location is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('Google Pagespeed upload location = %s' % pagespeed_upload)

# Remove any pagespeed data from today as this new data
# should override them
if not options.test:
    ql.remove_data('pagespeed_score')


# Check all domains and urls
tests = obtain_tests()
if not tests:
    logger.error('No pagespeed tests defined')
    ql.terminate()
else:
    for row in tests:
        t_id = row[0]
        t_domain = row[1]
        t_url = row[2]

        logger.info('Found a test: id:%s, domain:%s, url:%s' % (t_id,t_domain,t_url))

        query_pagespeed(t_id,t_domain,t_url,'desktop')
        query_pagespeed(t_id,t_domain,t_url,'mobile')


# All done
logger.info('All done with pagespeed tests')

# Disconnect from the DB server
qs.close()

# Remove the PID file
if (ql.remove_pid('%s/jobs/pid/pagespeed.pid' % settings.APP_DIR)):
    ql.terminate()

# Quit progam
exit(0)
