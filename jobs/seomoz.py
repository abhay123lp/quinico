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


"""Quinico SEOMoz Data Processor

   Requirements:
    - A properly configured Quinico environment (database, logging, configuration params)

"""


import os
import re
import hashlib
import hmac
import time
import base64
import logging
import json
import datetime
import urllib
import quinico
from optparse import OptionParser
from django.conf import settings
from qclasses import qemail
from qclasses import qsql
from qclasses import qlib


def query_urlmetrics(i_url):
    """
    Query the URL Metrics
    Try to grab all data (paid API access) and insert
    zeroes for all non-existent values
    """

    logger.info('Checking urlmetrics for %s' % i_url)
    base_url = 'http://lsapi.seomoz.com/linkscape/url-metrics/%s?%s'
    expires = int(time.time() + 300)
    sig = '%s\n%i' % (access_id, expires)
    signature = base64.b64encode(hmac.new(secret_key, sig, hashlib.sha1).digest())

    params = {}
    params['AccessID'] = access_id
    params['Expires'] = expires
    params['Signature'] = signature
    params['Cols'] = 133177540576
    url = base_url % (i_url.encode('utf-8'), urllib.urlencode(params))

    response = ql.http_request1('seomoz',url,1)
    if not response:
        return

    logger.debug(json.dumps(response))
    raw_json = json.loads(response)

    # This is the order in which we want to insert the data into the DB
    metrics = ['ueid','feid','peid','ujid','uifq','uipl','uid','fid','pid','umrp','fmrp','pmrp','utrp','ftrp','ptrp','uemrp','fejp','pejp','fjp','pjp','fuid','puid','fipl','upa','pda']

    # This is the ordered list of data we'll use for the SQL
    # We'll make this match the above data
    metrics_data = [i_url]

    # Cycle through the metrics and see if the metric was returned (if not, then the API account
    # is probably a free one so just insert zero
    # Also, convert to strings (with one sigfig, if appropriate)
    for metric in metrics:
        if metric in raw_json:
            logger.info('metric %s is there and has value %s' % (metric,raw_json[metric]))
            metrics_data.append(convert_metric(raw_json[metric]))
        else:
            metrics_data.append(str(0))

    # Save the data to the DB
    sql = """
       INSERT INTO seomoz_metrics (date,url_id,ueid,feid,peid,ujid,uifq,uipl,uid,fid,pid,umrp,fmrp,pmrp,utrp,ftrp,ptrp,uemrp,fejp,pejp,fjp,pjp,fuid,puid,fipl,upa,pda)
       VALUES (DATE(NOW()),
       (SELECT id from seomoz_url where url=%s),
       %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    if not options.test:
        qs.execute(sql,metrics_data)
        if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
            qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def query_meta():
    """
    Query the Metadata Metrics
    The API calls on this method do not count against allowed calls
    but count the errors
    """

    logger.info('Checking metadata')

    base_url = 'http://lsapi.seomoz.com/linkscape/metadata/last_update?%s'
    expires = int(time.time() + 300)
    sig = '%s\n%i' % (access_id, expires)
    signature = base64.b64encode(hmac.new(secret_key, sig, hashlib.sha1).digest())

    params = {}
    params['AccessID'] = access_id
    params['Expires'] = expires
    params['Signature'] = signature
    url = base_url % (urllib.urlencode(params))

    response = ql.http_request1('seomoz',url,1)
    if response:
        return int(response)
    else:
        return


def obtain_last_update():
    """
    Obtain the last data update date
    """
    logger.info('checking last time quinico updated data from seomoz')

    sql = """
            SELECT date 
            FROM seomoz_update
            ORDER BY id DESC 
            LIMIT 1"""

    (rowcount,rows) = qs.execute(sql)
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    if not rows:
        return 'none'
    else:
        # There is only one row and column
        return rows[0][0]


def convert_metric(metric):
    """
    Convert metric responses to appropriate strings
    """

    if re.match('^\d+\.\d+$',str(metric)):
       logger.info('converting to string with one sigfig')
       return str('%.1f' % metric)
    elif re.match('^\d+$',str(metric)):
       logger.info('converting to string')
       return str(metric)
    else:
       return metric


def obtain_urls():
    """
    Obtain a list of urls
    """

    logger.info('Looking for urls')

    # Create SQL statement
    sql = """
           SELECT url
           FROM seomoz_url"""

    (rowcount,rows) = qs.execute(sql)
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    # return the data
    return rows


def update_update():
    """
    Update the update table
    """

    logger.info('Updating the update table')

    # Create SQL statement
    sql = """
           INSERT INTO seomoz_update (date)
           VALUES (now())"""

    qs.execute(sql)
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


#
# BEGIN MAIN PROGRAM EXECUTION
#


# Parse Arguments
parser = OptionParser(description='SEOMoz query and data \
loading script', version='%prog 1.0')
parser.add_option('-f','--force',
                  action='store_true',
                  dest='force',
                  default=False,
                  help='Force data acquisition regardless of whether or not the seomoz index is old')
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
    qm.send('SEOMoz Test','Test message from the Quinico SEOMoz data collection job')
    exit(0)

# Create a qsql instance
qs = qsql.sql(host,user,password,name,logger)

# Create a qlib instance
ql = qlib.lib(qs,qm,settings.SMTP_NOTIFY_ERROR,logger)

# If we could not connect to MySQL, quit and notify someone
if qs.status != 0:
    ql.terminate()

# Check if another instance is already running
if ql.check_pid('%s/jobs/pid/seomoz.pid' % settings.APP_DIR):
    ql.terminate()

# Set a PID
if (ql.set_pid('%s/jobs/pid/seomoz.pid' % settings.APP_DIR)):
    ql.terminate()

# Let someone know we are starting data collection
logger.info('Started SEOMoz data collection job')
smtp_notify_data_start = int(ql.return_config('smtp_notify_data_start'))
if smtp_notify_data_start:
    qm.send('SEOMoz Job Starting','Starting Quinico SEOMoz data collection job')

# Obtain configuration parameters
# If we cannot obtain any of these, we have to quit

# SEOMoz access id (must be encoded as ascii for the hashing to work)
access_id = ql.return_config('seomoz_access_id')
access_id = access_id.encode('ascii')

if access_id is None:
    logger.error('SEOMoz Access ID is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('SEOmoz Access ID = %s' % access_id)

# SEOMoz secret key ((must be encoded as ascii for the hashing to work)
secret_key = ql.return_config('seomoz_secret_key')
secret_key = secret_key.encode('ascii')
if secret_key is None:
    logger.error('SEOMoz Secret Key is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('SEOmoz Secret Key = *****')

# Check when SEOMoz last updated data.  If its newer than our
# newest data, then perform the update, otherwise quit

# SEOMoz data about last update (this is an epoch)
sm_last_update = query_meta()
logger.info('Epoch return value from SEOMoz meta API: %s' % sm_last_update)

# If this is not working for some reason, we need to quit
if sm_last_update is None:
    ql.terminate()

# Quinico data about last update (this is a datetime object)
qu_last_update = obtain_last_update()
logger.info('Last Quinico update from SEOMoz (localtime): %s' % qu_last_update)
if qu_last_update == 'none':
    logger.info('SEOMoz statistics have never been updated, proceed to update data')
else:
    # Convert the localtime to UTC
    qu_last_update = ql.convert_date_utc(qu_last_update,settings.TIME_ZONE)
    logger.info('Last Quinico update from SEOMoz (UTC): %s' % qu_last_update)

    qu_epoch = time.mktime(qu_last_update.timetuple())
    logger.info('Last Quinico update from SEOMoz (UTC epoch): %s' % qu_epoch)

    # If the SEOMoz last update is newer than our last update (or force is requested), then proceed, otherwise exit
    if sm_last_update >= qu_epoch or options.force == True:
        logger.info('SEOMoz index is new or force is being requested, proceed to update data')
    else:
        logger.info('SEOMoz index is old, quiting')

        # Remove the PID file
        if (ql.remove_pid('%s/jobs/pid/seomoz.pid' % settings.APP_DIR)):
            ql.terminate()

        exit(0)

# If requested, let someone know
smtp_notify_seomoz_new = int(ql.return_config('smtp_notify_seomoz_new'))
if smtp_notify_seomoz_new:
    qm.send('SEOMoz Data Collection','SEOMoz data is being refreshed today')

# Remove any SEOMoz data from today as these new metrics
# should override them
if not options.test:
    ql.remove_data('seomoz_metrics')

# Obtain the list of urls to check
# Pause after each query b/c free accounts are rate limited
urls = obtain_urls()
if not urls:
    logger.error('No urls defined')
    ql.terminate()
else:
    for url in urls:
        # Query the API for url metrics
        query_urlmetrics(url[0])
        ql.pause(10)

# Update the seomoz_update table
if not options.test:
    update_update()

# All done
logger.info('All done with seomoz data checking')

# Disconnect from the DB server
qs.close()

# Remove the PID file
if (ql.remove_pid('%s/jobs/pid/seomoz.pid' % settings.APP_DIR)):
    ql.terminate()

# Quit progam
exit(0)
