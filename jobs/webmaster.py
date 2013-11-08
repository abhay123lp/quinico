#!/usr/bin/python

#
# Copyright 2013 - Tom Alessi
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
import pytz
import logging
import urllib
import urllib2
import json
import quinico
import datetime
import Queue
import threading
import time
import traceback
import requests
from xml.dom import minidom
from optparse import OptionParser
from django.conf import settings
from django.core.mail import send_mail
from qclasses import qemail
from qclasses import qsql
from qclasses import qlib


# -- GLOBALLY AVAILABLE -- #

# Google API key
google_key = ''

# Google Webmaster Username
google_wm_username = ''

# Google Webmaster Password
google_wm_password = ''

# Google Webmaster Auth Key
auth_key = ''

# Top Queries Date
check_date_tq = ''

# Grab the Quinico webapp settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'quinico.settings'

# Setup an instance of the Quinico logger
# Logging is thread-safe so all threads will share the same logger
logger = logging.getLogger('quinico')

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
                domain = row[0]

                # Google expects the domain to be preceeded with 'http://' and have a trailing '/'
                g_domain = 'http://%s/' % domain
                logger.debug('Google formatted domain is %s' % g_domain)

                # Check for keywords that we track in the webmaster search queries
                # If we don't have keywords for this domain, then don't bother
                keywords = obtain_keywords(qs,qm,domain) 

                if not keywords:
                    logger.debug('No keywords are defined for this domain - will not check Google search queries')
                else:
                    # Check for top search queries
                    query_webmaster_tq(qs,qm,ql,domain,keywords)

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
                errors,next_url = query_webmaster_api_ce(qm,ql,url,errors)

                # Keep processing pages of errors until there are not any
                process = True

                while process == True:
                    # If there is another page of results, request it
                    if next_url is None:
                        # No more entries, stop the loop
                        process = False
                    else:
                        # Make sure we have an auth_key (maybe it had to be reset)
                        if auth_key is None: 
                            # No auth key so we have to quit
                            ql.terminate()
                        else:
                            errors,next_url = query_webmaster_api_ce(qm,ql,next_url,errors)

                # Add the data
                for error in errors:

                    logger.debug('%s had a count of %s for %s' % (domain,errors[error],error))

                    # Make sure the error type exists in the DB
                    if not options.test:
                        add_error(qs,qm,error)

                    sql = """
                            INSERT INTO webmaster_crawl_error (date,domain_id,type_id,count)
                            VALUES (DATE(NOW()),
                            (SELECT id from webmaster_domain where domain=%s),
                            (SELECT id from webmaster_crawl_error_type where type=%s),
                            %s)"""

                    if not options.test:
                        qs.execute(sql,(domain,error,errors[error]))
                        if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
                            qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

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
                # Most likely there was a problem with the Pagespeed API
                # This generally should not happen as the function definitions that
                # that perform the work have their own exception handling
                logger.error('Exception encountered with thread %s: %s' % (t_name,traceback.format_exc()))
                if settings.SMTP_NOTIFY_ERROR:
                    qm.send('Error','Exception encountered with thread %s: %s' % (t_name,traceback.format_exc()))

                # Disconnect from the DB server
                qs.close()

                # Stop the thread
                break


def obtain_domains(qs,qm):
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


def obtain_keywords(qs,qm,domain):
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


def add_tq(qs,qm,domain,query,impressions,clicks):
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

    qs.execute(sql,(check_date_tq,domain,query,impressions,clicks))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def add_error(qs,qm,error):
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



def auth_webmaster(ql):
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

    global auth_key

    if match is None:
        logger.error('Could not determine the auth key')
        auth_key = None
    else:
        auth_key = match.group(1)


def send_urgent_messages(qs,ql,qm):
    """
    If there are any messages in the DB that are marked as urgent, acquire them
    and send out a status message
    """

    sql = """
        SELECT subject,date,date_discovered,first_name,last_name
        FROM webmaster_messages
        INNER JOIN auth_user on webmaster_messages.assignee_id=auth_user.id
        INNER JOIN webmaster_message_status on webmaster_messages.status_id=webmaster_message_status.id
        WHERE status=%s
        """

    (rowcount,rows) = qs.execute(sql,('urgent'))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    # Compose the message
    if rows:
        m = 'The following Google Webmaster messages are currently in urgent state:\n\n'

        # Dates are in UTC
        tz = pytz.timezone('Etc/UTC')

        for row in rows:
            m += '---\n'
            m += 'Subject: %s\nDate Discovered: %s\nDate Added: %s\nAssigned to: %s %s\n\n' % (row[0],
                                                                                               tz.localize(row[1]).astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%Y-%m-%d %H:%M:%S"),
                                                                                               tz.localize(row[2]).astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%Y-%m-%d %H:%M:%S"),
                                                                                               row[3],
                                                                                               row[4]
                                                                                              )

        send_mail('Quinico: Google Webmaster Urgent Messages', m, settings.SMTP_SENDER, [settings.SMTP_URGENT_MESSAGES], fail_silently=True)


def obtain_messages_patterns(qs,qm):
    """
    Obtain the Webmaster patterns that we want to match against so that 
    certain high priority messages can be assigned for follow-up
    """
    
    sql = """
           SELECT pattern,user_id
           FROM webmaster_message_pattern
          """
    
    (rowcount,rows) = qs.execute(sql)
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    # return the data
    return rows


def query_webmaster_api_messages(qs,ql,qm):
    """
    Query the Google Webmaster for any messages
    These queries are not domain specific as Google does not store
    them that way and the 'test' directive does not apply here
    """

    url = 'https://www.google.com/webmasters/tools/feeds/messages/'

    r = urllib2.Request(url)
    r.add_header('Authorization','GoogleLogin auth=%s' % auth_key)
    r.add_header('GData-Version','2')

    ATOM_NS = 'http://www.w3.org/2005/Atom'

    # Count the API Call
    ql.add_api_calls('webmaster',1)

    try:
        request = urllib2.urlopen(r)
    except urllib2.URLError, e:
        # Count the error
        ql.add_api_calls('webmaster',1,1)
        if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
            logger.error('Error acquiring Google Webmaster messages\nERROR:\n%s' % e)
            qm.send('Error','Error acquiring Google Webmaster messages\nERROR:\n%s' % e)
        
        # Cannot continue
        return

    response = request.read()
    request.close()

    # Obtain the XML from the response
    xml = minidom.parseString(response)

    # Obtain the list of patterns
    logger.debug('Obtaining messages patterns')
    patterns = obtain_messages_patterns(qs,qm)

    # Parse each message and add it to the queue, if it is unread
    for entry in xml.getElementsByTagNameNS(ATOM_NS, u'entry'):
            
        id = entry.getElementsByTagNameNS(ATOM_NS, u'id')[0].firstChild.data
        subject = entry.getElementsByTagName('wt:subject')[0].getAttribute('subject')
        body = entry.getElementsByTagName('wt:body')[0].getAttribute('body')
        date_discovered = entry.getElementsByTagName('wt:date')[0].firstChild.data
        read = entry.getElementsByTagName('wt:read')[0].firstChild.data

        logger.debug('Found a message (status:%s): %s' % (read,id))

        # If the message has not been read, add it to the Quinico DB and then mark it as read
        # in webmaster
        if read != 'true':

            # All messages will start with status of unread, unless there is a pattern match, in which case they are
            # marked as urgent
            message_status = 'unread'

            # Check if the message should be assigned to someone based on patterns (the first match gets the assignment)
            assignee = None
            for pattern in patterns:
                # The subject needs to match the pattern to be assigned
                logger.debug('Checking message against the following pattern: %s' % pattern[0])
                # Check the subject against the pattern
                if re.search(pattern[0],subject):
                    logger.debug('Pattern matched, assigning message to user id: %s' % pattern[1])
                    assignee = pattern[1]
                    message_status = 'urgent'
                    break

            # Convert the date to our server timezone and format
            date_now = ql.convert_datetime_now(settings.TIME_ZONE)
            date_discovered = ql.convert_datetime('Etc/UTC',date_discovered)

            # Add the message
            logger.debug('Adding webmaster message to database')

            sql = """
                  INSERT INTO webmaster_messages (date,date_discovered,subject,body,status_id,assignee_id)
                  VALUES (%s,%s,%s,%s,
                          (SELECT id from webmaster_message_status where status=%s),
                          %s)"""
            if not options.test:
                qs.execute(sql,(date_now,date_discovered,subject,body,message_status,assignee))
                # If there was an error adding to our database, then don't mark as read
                # we'll try to get it next time
                if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
                    qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))
                else:
                    # Mark as read
                    read_url = 'https://www.google.com/webmasters/tools/feeds/messages/%s' % urllib.quote_plus(id)
                    payload = """<?xml version="1.0" encoding="UTF-8"?>
                                
                                <atom:entry xmlns:atom='http://www.w3.org/2005/Atom' xmlns:wt="http://schemas.google.com/webmasters/tools/2007">
                                    <atom:id>%s</atom:id>
                                    <atom:category scheme='http://schemas.google.com/g/2005#kind'
                                        term='http://schemas.google.com/webmasters/tools/2007#message'>
                                    </atom:category>
                                    <wt:read>true</wt:read>
                                </atom:entry>"""

                    r_read = requests.put(read_url, 
                                          headers={
                                                 'Content-Type': ' application/atom+xml',
                                                 'Authorization': 'GoogleLogin auth=%s' % auth_key,
                                                 'GData-Version': '2'
                                                  },
                                          data=payload % id,
                                        )

                    logger.debug('Message read put status code: %s' % r_read.status_code)
                    logger.debug('Message read put response text: %s' % r_read.content)

        else:
            # Already read
            logger.debug('This message has already been read')
                

def query_webmaster_tq(qs,qm,ql,domain,keywords):
    """
    Query the Google Webmaster for the top search queries
    """

    logger.debug('Processing Google Webmaster Top Search Queries %s' % domain)

    url = 'https://www.google.com/webmasters/tools/downloads-list?hl=en&siteUrl=http%3A%2F%2F' + domain + '%2F'

    headers = {}
    headers['Authorization'] = 'GoogleLogin auth=%s' % auth_key
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
                    if query == keyword[0].encode('utf-8'):
                        # Get rid of commas in values
                        impressions = re.sub('[,<]','',impressions)
                        clicks = re.sub('[,<]','',clicks)
                        if not options.test:
                            add_tq(qs,qm,domain,keyword[0],impressions,clicks)

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


def query_webmaster_api_ce(qm,ql,url,errors):
    """
    Query the Google Webmaster API for Crawl Errors
    """

    logger.debug('Processing next url: %s' % (url))

    r = urllib2.Request(url)
    r.add_header('Authorization','GoogleLogin auth=%s' % auth_key)
    r.add_header('GData-Version','2')

    ATOM_NS = 'http://www.w3.org/2005/Atom'

    # Count the API Call
    ql.add_api_calls('webmaster',1)

    try:
        request = urllib2.urlopen(r)
    except urllib2.URLError, e:
       # Count the error
       ql.add_api_calls('webmaster',1,1)

       logger.error('error encountered requesting url %s : %s' % (url,e))
       if settings.SMTP_NOTIFY_ERROR:
           qm.send('Error','error encountered requesting url %s : %s' % (url,e))

       # If the error is a 403, then re-auth, the auth token may have expired.  Try again w/ the same URL
       if re.match(r'403',str(e.code)):
           logger.error('403 error detected - attempting to re-auth to Google ClientLogin Service')
           ql.pause(30)
           auth_webmaster(ql) 
           return errors,url

       # If the error is a 500, then wait a bit and then try again w/ the same URL
       if re.match(r'5(.*)',str(e.code)):
           logger.error('5xx error detected - will wait a bit and try again with the same url')
           ql.pause(30)
           return errors,url

       # Anything else, just return b/c we don't know how to handle this
       logger.error('Unknown error detected - stopping further processing on this domain')
       return errors,None

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
    return errors,next_url


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
        qm.send('Webmaster Test','Test message from the Quinico Webmaster data collection job')
        exit(0)

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

    # Google API key
    global google_key
    google_key = ql.return_config('google_key')
    if google_key is None:
        logger.error('Google Key is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.debug('Google Key = %s' % google_key)

    # Google Webmaster Username
    global google_wm_username
    google_wm_username = ql.return_config('google_wm_username')
    if google_wm_username is None:
        logger.error('Google Webmaster username is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.debug('Google Webmaster username = %s' % google_wm_username)

    # Google Webmaster Password
    global google_wm_password
    google_wm_password = ql.return_config('google_wm_password')
    if google_wm_password is None:
        logger.error('Google Webmaster password is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.debug('Google Webmaster password = *****')

    # Webmaster Threads
    webmaster_threads = ql.return_config('webmaster_threads')
    if webmaster_threads is None:
        logger.error('Google Webmaster threads is not defined, perhaps someone deleted it')
        ql.terminate()
    else:
       logger.info('Google Webmaster threads = %s' % webmaster_threads)


    # Top Queries Date (We'll check the data from two days ago, each day)
    global check_date_tq
    check_date_tq = ql.get_date(2)
    logger.debug('Date to check Google top query data entries against: %s' % check_date_tq)

    # Remove any webmaster data for our check_dates as this new data
    # should override them
    if not options.test:
        ql.remove_data('webmaster_crawl_error')
        ql.remove_data('webmaster_top_search_queries',check_date_tq)

    # Set the Google Auth Key
    auth_webmaster(ql)
    if auth_key is None:
        logger.error('Could not obtain Google auth_key')
        ql.terminate()


    # Check the Google messages queue first, as that part is easy and quick
    # All other Google data queries will be threaded so they can progress faster
    query_webmaster_api_messages(qs,ql,qm)

    # Sent a summary email of all urgent messages
    send_urgent_messages(qs,ql,qm)

    # Check all domains for crawl errors - we'll perform the tests serially so as not to overload the API
    domains = obtain_domains(qs,qm)

    if not domains:
        logger.error('No domains defined')
        ql.terminate()
    else:
        # Create a queue for the tests
        queue = Queue.Queue()

        for row in domains:
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

        for i in range(int(webmaster_threads)):
            # Create a worker and pass it the queue
            w = Worker(queue)

            # Start the worker
            w.start()

        # If all threads except this one are done, then quit
        # Check at 1 second intervals
        while threading.active_count() > 1:
            time.sleep(1)

    # All done
    logger.info('All done with webmaster data processing')

    # Disconnect from the DB server
    qs.close()

    # Remove the PID file
    if (ql.remove_pid('%s/jobs/pid/webmaster.pid' % settings.APP_DIR)):
        ql.terminate()


# This program can only run is executed directly
if __name__ == "__main__":

    # Run main program
    main()

    # Quit program
    exit(0)

