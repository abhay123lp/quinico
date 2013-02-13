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


"""Quinico Keyword Rank Data Processor

   Requirements:
    - A properly configured Quinico environment (database, logging, configuration params)

"""


import os
import logging
import quinico
import urllib
import json
from optparse import OptionParser
from django.conf import settings
from qclasses import qemail
from qclasses import qsql
from qclasses import qlib


def add_top_ten(domain,keyword,url,rank):
    """
    Add a top_ten URL rank
    """

    logger.info('Adding a top 10 url: %s, %s, %s, %s' % (domain,keyword,url,rank))

    sql = """
           INSERT INTO keyword_rank_top_ten (date,domain_id,keyword_id,url_id,rank)
           VALUES (DATE(NOW()),
           (SELECT id from keyword_rank_domain where domain=%s),
           (SELECT id from keyword_rank_keyword where keyword=%s),
           (SELECT id from keyword_rank_url where url=%s),
           %s)"""

    qs.execute(sql,(domain,keyword,url,rank))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def add_url(url):
    """
    Add a URL
    """

    logger.info('Adding URL to database: %s' % url)

    sql = """
           INSERT INTO keyword_rank_url (url)
           SELECT %s
           FROM dual
           WHERE not exists (SELECT * from keyword_rank_url WHERE url=%s)"""

    qs.execute(sql,(url,url))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def add_rank(domain,keyword,rank,url):
    """
    Add a keyword rank
    """

    logger.info('Saving Rank: domain:%s, keyword:%s, rank:%s, url:%s' % (domain,keyword,rank,url))

    sql = """
           INSERT INTO keyword_rank_rank (date,domain_id,keyword_id,url_id,rank) 
           VALUES (DATE(NOW()),
           (SELECT id from keyword_rank_domain where domain=%s),
           (SELECT id from keyword_rank_keyword where keyword=%s),
           (SELECT id from keyword_rank_url where url=%s),
           %s)"""

    qs.execute(sql,(domain,keyword,url,rank))
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))


def obtain_domains():
    """
    Obtain a list of domains that are in the system
    """

    logger.info('Looking for domains')

    # Create SQL statement
    sql = """
           SELECT domain,gl,googlehost
           FROM keyword_rank_domain"""

    (rowcount,rows) = qs.execute(sql)
    if qs.status != 0 and settings.SMTP_NOTIFY_ERROR:
        qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,qs.emessage))

    # return the data
    return rows


def obtain_keywords(domain):
    """
    Obtain a list of keywords, given a domain
    """

    logger.info('Looking for keywords for %s' % domain)

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


def obtain_ranking(domain,gl,googlehost,keyword,google_key,google_se_id,max_results,max_api_calls):
    """
    Query the Google Search API
    """

    # Total queries
    counter = 1

    # Top 10 search results
    top_ten = []

    # configs are stored as varchars in the DB so convert them to ints
    max_results = int(max_results)
    max_api_calls = int(max_api_calls)

    logger.info('Checking %s for keyword %s with max results %i' % (domain,keyword,max_results))

    # Determine how many api calls we currently have for today
    current_api_calls = ql.count_api_calls('keyword_rank')

    # Construct the initial request and urlencode the keyword
    keyword_enc = urllib.urlencode({'q':keyword.encode('utf-8')})
    url = 'https://www.googleapis.com/customsearch/v1?'
    url += 'key=' + google_key + '&'
    url += 'cx=' + google_se_id + '&'
    url += '%s&num=10&ie=utf8&oe=utf8&' % keyword_enc
    url += 'gl=%s&' % gl
    url += 'googlehost=%s' % googlehost
  
    # We are only going to check a certain number of user configurable 
    # search results
    while counter < max_results:

        # If we are maxed out on API requests for the day, don't make any more b/c this costs $$
        if current_api_calls >= max_api_calls:
           logger.info('API calls are maxed out for today')
           return (0,'none',top_ten)

        response = ql.http_request1('keyword_rank',url,1)
        # If there was an error in requesting results, we have to quit and send back nothing
        if not response:
            return (0,'none',top_ten)

        # Count how many api calls we currently have
        current_api_calls = ql.count_api_calls('keyword_rank')

        logger.debug(json.dumps(response))
        raw_json = json.loads(response)

        for d in json.loads(response):
            logger.info('Found JSON item: %s' % d)

        total_results = raw_json['searchInformation']['totalResults']

        # Parse the results (this will be skipped if there are no results)
        results = raw_json['items']

        # If this is the first set of results, save the top 10
        if (counter == 1):
            for i in results:
                top_ten.append(i['link'])

        # Now check the results for our domain
        for i in results:
            logger.info('Search result:%s, domain:%s, url:%s' % (counter,i['displayLink'],i['link']))
            # If we get a match, return
            if i['displayLink'] == domain:
               logger.info('Got a match!')
               return (counter,i['link'],top_ten)
            else:
               # no match
               counter += 1

        # Don't request more results than Google says they have
        if counter >= total_results:
            return (0,'none',top_ten)
        else:
            url = 'https://www.googleapis.com/customsearch/v1?'
            url += 'key=' + google_key + '&'
            url += 'cx=' + google_se_id + '&'
            url += '%s&num=10&ie=utf8&oe=utf8&' % keyword_enc
            url += 'gl=%s&' % gl
            url += 'googlehost=%s&' % googlehost
            url += 'start=' + str(counter)

    # Looks like we didn't find a result
    logger.info('Result not found within ' + str(max_results))

    return (0,'none',top_ten)



#
# BEGIN MAIN PROGRAM EXECUTION
#


# Parse Arguments
parser = OptionParser(description='Google keyword rank query \
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
    qm.send('Keyword Rank Test','Test message from the Quinico Keyword Rank data collection job')
    exit(0)

# Create a qsql instance
qs = qsql.sql(host,user,password,name,logger)

# Create a qlib instance
ql = qlib.lib(qs,qm,settings.SMTP_NOTIFY_ERROR,logger)

# If we could not connect to MySQL, quit and notify someone
if qs.status != 0:
    ql.terminate()

# Check if another instance is already running
if ql.check_pid('%s/jobs/pid/keyword_rank.pid' % settings.APP_DIR):
    ql.terminate()

# Set a PID
if (ql.set_pid('%s/jobs/pid/keyword_rank.pid' % settings.APP_DIR)):
    ql.terminate()

# Let someone know we are starting data collection
logger.info('Started Keyword Rank data collection job')
smtp_notify_data_start = int(ql.return_config('smtp_notify_data_start'))
if smtp_notify_data_start:
    qm.send('Keyword Rank Job Starting','Starting Quinico Keyword Rank data collection job')

# Obtain configuration parameters
# If we cannot obtain any of these, we have to quit

# Google key
google_key = ql.return_config('google_key')
if google_key is None:
    logger.error('Google Key is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('Google Key = %s' % google_key)

# Google Search Engine ID
google_se_id = ql.return_config('google_se_id')
if google_se_id is None:
    logger.error('Google Search Engine ID is not defined, perhaps someone deleted it')
    ql.terminate()
else:
   logger.info('Google Search Engine ID = %s' % google_se_id)

# Max search results
max_results = ql.return_config('max_keyword_results')
if max_results is None:
    logger.error('Max Keyword Results is not defined, perhaps someone deleted it')
    ql.terminate()
else:
    logger.info('Max Keyword Results = %s' % max_results)

# Max Google API calls
max_api_calls = ql.return_config('max_google_api_calls')
if max_api_calls is None:
    logger.error('Max Google API calls is not defined, perhaps someone deleted it')
    ql.terminate()
else:
    logger.info('Max Google API calls = %s' % max_api_calls)


# Remove any keyword rankings from today as these new
# rankings should override them
if not options.test:
    ql.remove_data('keyword_rank_rank')
    ql.remove_data('keyword_rank_top_ten')


# Check all keywords
d_rows = obtain_domains()
if not d_rows:
    logger.error('No domains defined')
    ql.terminate()
else:
    for d_row in d_rows:

        domain = d_row[0]
        gl = d_row[1]
        googlehost = d_row[2]
        logger.info('Found a domain: %s with gl: %s and googlehost: %s - now looking for keywords' % (domain,gl,googlehost))
        k_rows = obtain_keywords(domain)

        if not k_rows:
            logger.warning('No keywords defined for %s' % domain)
        else:
            for k_row in k_rows:
                keyword = k_row[0]
                logger.info('Found a keyword: %s, now processing rankings' % (keyword))
                (rank,url,top_ten) = obtain_ranking(domain,
						    gl,
                                                    googlehost,
                                                    keyword,
                                                    google_key,
                                                    google_se_id,
                                                    max_results,
                                                    max_api_calls)
                logger.info('Rank: %s, URL: %s' % (str(rank),url))

                # Produce a utf-8 byte string
                url = url.encode('utf-8')

                # Add the url
                if not options.test:
                    add_url(url)

                # Add the rank
                if not options.test:
                    add_rank(domain,keyword,rank,url)

                logger.info('Adding the top ten urls for the keyword')
                top_rank = 1
                for top_url in top_ten:

                    # Produce a utf-8 byte string
                    top_url = top_url.encode('utf-8')

                    # Add the URL
                    if not options.test:
                        add_url(top_url)

                    # Add the position
                    if not options.test:
                        add_top_ten(domain,keyword,top_url,top_rank)

                    top_rank += 1


# All done
logger.info('All done with keyword rank checking')

# Disconnect from the DB server
qs.close()

# Remove the PID file
if (ql.remove_pid('%s/jobs/pid/keyword_rank.pid' % settings.APP_DIR)):
    ql.terminate()

# Quit progam
exit(0)
