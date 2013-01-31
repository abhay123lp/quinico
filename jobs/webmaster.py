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


"""Quinico Google Webmaster Data Processor

   Requirements:
    - A properly configured Quinico environment (database, logging, configuration params)

"""


import os
import re
import csv
import logging
import urllib
import urllib2
import json
import quinico
from xml.dom import minidom
from optparse import OptionParser
from django.conf import settings
from qclasses import qemail
from qclasses import qsql
from qclasses import qlib


def obtain_domains():
    """
    Obtain a list of domains to check
    """

    logger.debug('Looking for domains')

    # Create SQL statement
    sql = """
           SELECT domain
           FROM webmaster_domain
          """

    (rowcount,rows) = qs.execute(sql)
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    # return the data
    return rows


def obtain_keywords(domain):
    """
    Obtain a list of keywords, given a domain
    """

    logger.info('Looking for keywords for ' + domain)

    # Create SQL statement
    sql = """
           SELECT keyword
           FROM keyword_rank_test
           INNER JOIN keyword_rank_domain on keyword_rank_test.domain_id=keyword_rank_domain.id
           INNER JOIN keyword_rank_keyword on keyword_rank_test.keyword_id=keyword_rank_keyword.id
           WHERE domain=%s"""

    (rowcount,rows) = qs.execute(sql,(domain))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    # return the data
    return rows


def add_tq(d_tq,domain,query,impressions,clicks):
    """
    Add top query
    """

    logger.debug('Adding webmaster top_query to database for domain: %s' % (domain))

    sql = """
             INSERT INTO webmaster_top_search_queries (date,domain_id,keyword_id,impressions,clicks)
             VALUES (
                %s,
                (SELECT id from webmaster_domain where domain=%s),
                (SELECT id from keyword_rank_keyword where keyword=%s),
                %s,
                %s
             )"""

    qs.execute(sql,(d_tq,domain,query,impressions,clicks))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def add_message(message):
    """
    Add a message type
    """

    logger.debug('Adding message type to database: %s' % message)

    sql = """
           INSERT INTO webmaster_message_type (type)
           SELECT %s
           FROM dual
           WHERE not exists (SELECT * from webmaster_message_type WHERE type=%s)"""

    qs.execute(sql,(message,message))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def add_error(error):
    """
    Add an error type
    """

    logger.debug('Adding error type to database: %s' % error)

    sql = """
           INSERT INTO webmaster_crawl_error_type (type)
           SELECT %s
           FROM dual
           WHERE not exists (SELECT * from webmaster_crawl_error_type WHERE type=%s)"""

    qs.execute(sql,(error,error))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))



def auth_webmaster():
    """
    Query the Google login service and obtain an auth token
    """

    logger.debug('Authenticating to webmaster')

    base_url = 'https://www.google.com/accounts/ClientLogin?%s'
    params = {}
    params['Email'] = google_wm_username
    params['Passwd'] = google_wm_password
    params['service'] = 'sitemaps'
    url = base_url % (urllib.urlencode(params))

    response = ql.http_request1('webmaster',url,1)
    if not response:
        return None

    # Find the auth string
    match = re.search('Auth=(.*)\n',response)

    if match is None:
        return None
    else:
        authKey = match.group(1)
        return authKey


def query_webmaster_tq(domain,key,keywords,d_tq):
    """
    Query the Google Webmaster for the top search queries
    """

    logger.debug('Processing Google Webmaster Top Search Queries %s' % domain)

    url = 'https://www.google.com/webmasters/tools/downloads-list?hl=en&siteUrl=http%3A%2F%2F' + domain + '%2F'

    headers = {}
    headers['Authorization'] = 'GoogleLogin auth=%s' % key
    headers['GData-Version'] = 2

    # Make the HTTP request
    response = ql.http_request2('webmaster',url,headers,None,1)

    # If there was an error, bail
    if not response:
        return

    logger.debug(json.dumps(response))
    raw_json = json.loads(response)

    # Strip the hyphens out of the date
    check_date_tq_bare = re.sub('-','',check_date_tq)

    top_queries_url = 'https://www.google.com' + raw_json['TOP_QUERIES'] + '&prop=ALL&region&db=%s&de=%s' % (check_date_tq_bare,check_date_tq_bare)

    # Make the HTTP request
    response1 = ql.http_request2('webmaster',top_queries_url,headers,1,1)

    # If there was an error, bail
    if not response1:
        return

    raw_csv = csv.reader(response1)
    for row in raw_csv:
        # If the row is empty, just skip it, or maybe the CSV is empty
        # There should be 8 columns:
        # [impressions][change][clicks][change][ctr][change][av pos][change]
        if len(row) == 9: 
            try:
                query = row[0]
                impressions = row[1]
                clicks = row[3]

                # We need to check each row against our keywords
                for keyword in keywords:
                    if query == keyword[0].decode('utf-8').encode('utf-8'):
                        # Get rid of commas in values
                        impressions = re.sub('[,<]','',impressions)
                        clicks = re.sub('[,<]','',clicks)
                        if not options.test:
                            add_tq(d_tq,domain,keyword[0],impressions,clicks)

            except ValueError, ve:
                # Log it and count the error
                logger.error('Error encountered parsing Google Webmaster CSV: %s' % ve)
                ql.add_api_calls('webmaster',1,1)

            except IndexError, ie:
                # Log it and count the error
                logger.error('Error encountered parsing Google Webmaster CSV: %s' % ie)
                ql.add_api_calls('webmaster',1,1)
        else:
                logger.debug('Empty row detected in Google webmaster CSV for domain: %s' % domain)


def query_webmaster_api_me(key,check_date):
    """
    Query the Google Webmaster API for Messages
    """

    messages = []

    url = 'https://www.google.com/webmasters/tools/feeds/messages/'
    ATOM_NS = 'http://www.w3.org/2005/Atom'

    headers = {}
    headers['Authorization'] = 'GoogleLogin auth=%s' % key
    headers['GData-Version'] = 2

    # Make the HTTP request
    response = ql.http_request2('webmaster',url,headers,None,1)

    # If there was an error, bail
    if not response:
        return

    xml = minidom.parseString(response)

    for entry in xml.getElementsByTagNameNS(ATOM_NS, u'entry'):
        # Check when this message was posted
        date_added = entry.getElementsByTagName('wt:date')[0].firstChild.data
        logger.debug('Entry date in UTC is %s' % date_added)
        date_added_formatted = ql.convert_date(settings.TIME_ZONE,date_added)
        logger.debug('Formatted entry date in %s is %s' % (settings.TIME_ZONE,date_added_formatted))

        if date_added_formatted == check_date:
            logger.debug('Date matches, message will be counted')
            messages.append(entry.getElementsByTagName('wt:subject')[0].getAttribute('subject'))
        else:
            logger.debug('Date does not match, message will be skipped')

    return messages


def query_webmaster_api_ce(url,key,errors):
    """
    Query the Google Webmaster API for Crawl Errors
    """

    logger.debug('Processing next url: %s' % (url))

    r = urllib2.Request(url)
    r.add_header('Authorization','GoogleLogin auth=%s' % key)
    r.add_header('GData-Version','2')

    ATOM_NS = 'http://www.w3.org/2005/Atom'

    # Count the API Call
    ql.add_api_calls('webmaster',1)

    try:
        request = urllib2.urlopen(r)
    except urllib2.URLError, e:
       # Count the error
       ql.add_api_calls('webmaster',1,1)

       logger.error('error encountered requesting url: %s' % e)
       if settings.SMTP_NOTIFY_ERROR:
           qm.send('Error','error encountered requesting url: %s' % e)

       # If the error is a 403, then re-auth, the auth token may have expired.  Try again w/ the same URL
       if re.match(r'403',str(e.code)):
           logger.error('403 error detected - attempting to re-auth to Google ClientLogin Service')
           ql.pause(30)
           key = auth_webmaster() 
           return errors,key,url

       # If the error is a 500, then wait a bit and then try again w/ the same URL
       if re.match(r'5(.*)',str(e.code)):
           logger.error('5xx error detected - will wait a bit and try again with the same url')
           ql.pause(30)
           return errors,key,url

       # Anything else, just return b/c we don't know how to handle this
       logger.error('Unknown error detected - stopping further processing on this domain')
       return errors,key,None

    response = request.read()
    request.close()

    xml = minidom.parseString(response)

    # Assume there is no next_url
    next_url = None

    # Get the next link, if there is one
    for link in xml.getElementsByTagNameNS(ATOM_NS, u'link'):
        if link.getAttribute('rel') == 'next':
            next_url = link.getAttribute('href')
            logger.debug('Next url: %s' % next_url)
            break

    # We'll count every error, regardless of when it was first detected
    for entry in xml.getElementsByTagNameNS(ATOM_NS, u'entry'):
        # Add the error type if its not already part of our dict
        if not entry.getElementsByTagName('wt:detail')[0].firstChild.data in errors:
            errors[entry.getElementsByTagName('wt:detail')[0].firstChild.data] = 1
        else:
            errors[entry.getElementsByTagName('wt:detail')[0].firstChild.data] += 1

    logger.debug('Errors are now: %s' % errors)
    return errors,key,next_url



#
# BEGIN MAIN PROGRAM EXECUTION
#


# Parse Arguments
parser = OptionParser(description='Google Webmaster query \
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
    qm.send('Webmaster Test','Test message from the Quinico Webmaster data collection job')
    exit(0)

# Create a qsql instance
qs = qsql.sql(host,user,password,name,logger)

# Create a qlib instance
ql = qlib.lib(qs,qm,settings.SMTP_NOTIFY_ERROR,logger)

# If we could not connect to MySQL, quit and notify someone
if qs.status != 0:
    ql.terminate()

# Check if another instance is already running
if ql.check_pid('%s/jobs/pid/webmaster.pid' % settings.APP_DIR):
    ql.terminate()

# Set a PID
if (ql.set_pid('%s/jobs/pid/webmaster.pid' % settings.APP_DIR)):
    ql.terminate()

# Let someone know we are starting data collection
logger.info('Started Webmaster data collection job')
smtp_notify_data_start = int(ql.return_config('smtp_notify_data_start'))
if smtp_notify_data_start:
    qm.send('Webmaster Job Starting','Starting Quinico Webmaster data collection job')

# Obtain configuration parameters
# If we cannot obtain any of these, we have to quit

# Google Application key
google_key = ql.return_config('google_key')
if google_key is None:
    logger.error('Google Key is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.debug('Google Key = %s' % google_key)

# Google Webmaster Username
google_wm_username = ql.return_config('google_wm_username')
if google_wm_username is None:
    logger.error('Google Webmaster username is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.debug('Google Webmaster username = %s' % google_wm_username)

# Google Webmaster Password
google_wm_password = ql.return_config('google_wm_password')
if google_wm_password is None:
    logger.error('Google Webmaster password is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.debug('Google Webmaster password = ********')

# Today's date
# We will count everything in the index each day and add it to the Quinico DB as today
# (except for top search queries)
check_date = ql.get_date(0)
logger.debug('Date to check Google crawl data entries against: %s' % check_date)

# Top Queries Data (We'll check the data from two days ago, each day)
check_date_tq = ql.get_date(2)
logger.debug('Date to check Google top query data entries against: %s' % check_date_tq)


# Remove any webmaster data for our check_dates as this new data
# should override them
if not options.test:
    logger.debug('Removing data from database for previous runs on this day')
    ql.remove_data('webmaster_crawl_error',check_date)
    ql.remove_data('webmaster_message',check_date)
    ql.remove_data('webmaster_top_search_queries',check_date_tq)


# Obtain the Google Auth Key
authKey = auth_webmaster()
if authKey is None:
    logger.error('Could not obtain Google authKey')
    ql.terminate()


# Check for messages (this is not domain specific)
# messages = query_webmaster_api_me(authKey,check_date)
messages = None
if messages:
    for message in messages:
        # Make sure the message type exists in the DB
        if not options.test:
            add_message(message)

        sql = """
            INSERT INTO webmaster_message (date,type_id)
            VALUES (
            %s,
            (SELECT id from webmaster_message_type where type=%s))
        """

        if not options.test:
            qs.execute(sql,(check_date,message))
            if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
                qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


# Check all domains - we'll perform the tests serially so as not to overload the API
domains = obtain_domains()

if not domains:
    logger.error('No domains defined')
    ql.terminate()
else:
    for row in domains:
        domain = row[0]

        # Google expects the domain to be preceeded with 'http://' and have a trailing '/'
        g_domain = 'http://%s/' % domain
        logger.debug('Google formatted domain is %s' % g_domain)

        # Check for keywords that we track in the webmaster search queries
        # If we don't have keywords for this domain, then don't bother
        keywords = obtain_keywords(domain) 
        if not keywords:
            logger.debug('No keywords are defined for this domain - will not check Google search queries')
        else:
            # Check for top search queries
            query_webmaster_tq(domain,authKey,keywords,check_date_tq)

        # Check for crawl errors
        logger.debug('Checking %s for crawl errors' % domain)
        
        # This will default to 100 results per query (no way to increase this) 
        base_url = 'https://www.google.com/webmasters/tools/feeds/%s/crawlissues/'
        url = base_url % urllib.quote_plus(g_domain)

        # Dictionary to hold all errors
        errors = {}

        # Assume there is only one page of errors, if any
        next_url = None

        # Process individual errors
        errors,authKey,next_url = query_webmaster_api_ce(url,authKey,errors)

        # Keep processing pages of errors until there are not any
        process = True

        while process == True:
            # If there is another page of results, request it
            if not next_url is None:
                # If we had to reset the authKey, make sure it is not None
                if not authKey is None: 
                    errors,authKey,next_url = query_webmaster_api_ce(next_url,authKey,errors)
            else:
                # No more entries, stop the loop
                process = False

        # Add the data
        for error in errors:

            logger.debug('%s had a count of %s for %s' % (domain,errors[error],error))

            # Make sure the error type exists in the DB
            if not options.test:
                add_error(error)

            sql = """
                    INSERT INTO webmaster_crawl_error (date,domain_id,type_id,count)
                    VALUES (
                    %s,
                    (SELECT id from webmaster_domain where domain=%s),
                    (SELECT id from webmaster_crawl_error_type where type=%s),
                    %s)
                  """

            if not options.test:
                qs.execute(sql,(check_date,domain,error,errors[error]))
                if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
                    qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


# All done
logger.warning('Finished processing Webmaster data')

# Disconnect from the DB server
qs.close()

# Remove the PID file
if (ql.remove_pid('%s/jobs/pid/webmaster.pid' % settings.APP_DIR)):
    ql.terminate()

# Quit progam
exit(0)
