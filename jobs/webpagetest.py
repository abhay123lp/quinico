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
import xml.etree.ElementTree as ET
from optparse import OptionParser
from django.conf import settings
from qclasses import qemail
from qclasses import qsql
from qclasses import qlib


def obtain_tests():
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


def query_webpagetest(t_id,domain,u,l):
    """
    Query the Web Page Test API
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
        
        test_status_code = check_status(status_url)
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

    # Sometimes either view1 or view2 failed during the test
    try:
       view1 = xml.findall('./data/successfulFVRuns')[0].text 
       view2 = xml.findall('./data/successfulRVRuns')[0].text 
       logger.debug('Successful FV:%s, Successful RV:%s' % (view1,view2))
    except Exception as e:
        logger.warning('Error encountered searching for FV or RV status for %s : %s : %s.' % (domain,xml_url,e))

    # Create a datetime object for right now
    time_now = datetime.datetime.now()

    # Add the server's timezone and then convert to UTC before adding to the DB
    time_now = ql.convert_date_utc(time_now,settings.TIME_ZONE)

    # List of metrics we are tracking
    output_values = ['loadTime','TTFB','bytesOut','bytesOutDoc','bytesIn','bytesInDoc','connections','requests','requestsDoc','responses_200','responses_404','responses_other','result','render','fullyLoaded','cached','docTime','domTime','score_cache','score_cdn','score_gzip','score_cookies','score_keep-alive','score_minify','score_combine','score_compress','score_etags','gzip_total','gzip_savings','minify_total','minify_savings','image_total','image_savings','aft','domElements']

    # We are doing only one run with a repeat view
    for view in [1,2]:

        if view == 1:
           view_num = 'firstView'
        elif view == 2:
           view_num = 'repeatView'

        values = []

        # Add the values we know about
        values.append(time_now)
        values.append(t_id)
        values.append(testId)
        values.append(view)

        # Run through the values we are looking for from WPT (if they are not there, errors are raised)
        for output_value in output_values:
            try:
                values.append(xml.findall('./data/run/%s/results/%s' % (view_num,output_value))[0].text)
            except Exception as e:
                # The value was not there, so add a zero
                values.append(0)
                logger.warning('Error encountered searching for %s in view %s for %s:nError: %s,Url: %s' % (output_value,view,domain,e,xml_url))

        sql = """
           INSERT INTO webpagetest_score (date,test_id,testId,viewNumber,loadTime,ttfb,bytesOut,bytesOutDoc,bytesIn,bytesInDoc,connections,requests,requestsDoc,responses_200,responses_404,responses_other,result,render,fullyLoaded,cached,docTime,domTime,score_cache,score_cdn,score_gzip,score_cookies,score_keep_alive,score_minify,score_combine,score_compress,score_etags,gzip_total,gzip_savings,minify_total,minify_savings,image_total,image_savings,aft,domElements)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        if not options.test:
            qs.execute(sql,values)
            if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
                qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def check_status(url):
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


#
# BEGIN MAIN PROGRAM EXECUTION
#


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
    qm.send('Webpagetest Test','Test message from the Quinico Webpagetest data collection job')
    exit(0)

# Create a qsql instance
qs = qsql.sql(host,user,password,name,logger)

# Create a qlib instance
ql = qlib.lib(qs,qm,settings.SMTP_NOTIFY_ERROR,logger)

# If we could not connect to MySQL, quit and notify someone
if qs.status != 0:
    ql.terminate()

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
wpt_key = ql.return_config('wpt_key')
if wpt_key is None:
    logger.error('wpt_key is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('wpt_key = %s' % wpt_key)

# Max attempts per test
wpt_attempts = ql.return_config('wpt_attempts')
if wpt_attempts is None:
    logger.error('wpt_attempts is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('wpt_attempts = %s' % wpt_attempts)

# Max wait between status checks
wpt_wait = ql.return_config('wpt_wait')
if wpt_wait is None:
    logger.error('wpt_wait is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('wpt_wait = %s' % wpt_wait)


# Check all domains and urls
# We'll perform the tests serially so as not to overload the API
tests = obtain_tests()
if not tests:
    logger.error('No webpagetests defined')
    terminate()
else:
    for row in tests:
        t_id = row[0]
        t_domain = row[1]
        t_url = row[2]
        t_location = row[3]
        
        logger.info('Found a test: id:%s, domain:%s, url:%s, location:%s' % (t_id,t_domain,t_url,t_location))
        query_webpagetest(t_id,t_domain,t_url,t_location)


# All done
logger.info('All done with webpagetest tests')

# Disconnect from the DB server
qs.close()

# Remove the PID file
if (ql.remove_pid('%s/jobs/pid/webpagetest.pid' % settings.APP_DIR)):
    ql.terminate()

# Quit progam
exit(0)
