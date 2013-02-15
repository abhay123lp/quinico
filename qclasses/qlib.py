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


"""Miscellaneous shared methods class for Quinico

   Requirements:
    1. A properly configured logger
    2. An instance of qsql
    3. An instance of qemail

"""

import os
import pytz
import datetime
import time
import urllib
import urllib2
import uuid


class lib:

    Name = "qlib"

    def __init__(self, qs, qm, notify_error, logger):
        """
        Constructor
        """

        self.qm = qm
        self.qs = qs
        self.notify_error = notify_error
        self.logger = logger


    def return_config(self,option):
        """
        Return a configuration parameter
        """

        self.logger.info('Looking for option: %s' % option)

        # Create SQL statement
        sql = """
               SELECT config_value
               FROM main_config
               WHERE config_name=%s"""

        (rowcount,rows) = self.qs.execute(sql,(option))
        if self.qs.status != 0:
            if self.notify_error:
                self.qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,self.qs.emessage))

        if rowcount == 0:
           return
        else:
           return rows[0][0]


    def remove_data(self,table,d=None):
        """
        Remove data from a table from today
        """

        # Create SQL statement
        if d is None:
            self.logger.info('Removing pre-existing data from %s for today' % table)
            sql = 'DELETE FROM ' + table + ' WHERE date=DATE(NOW())'
            self.qs.execute(sql)
        else:
            self.logger.info('Removing pre-existing data from %s for %s' % (table,d))
            sql = 'DELETE FROM ' + table + ' WHERE date=%s'
            self.qs.execute(sql,(d))

        if self.qs.status != 0:
            if self.notify_error:
                self.qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,self.qs.emessage))


    def count_api_calls(self,table,error=None):
        """
        Count the number of API calls or errors for today
        """

        # Counting errors
        if error == 1:
            self.logger.info('Counting current API errors for %s for today' % table)
            table += '_api_errors'
        # Counting API calls
        else:
            self.logger.info('Counting current API calls for %s for today' % table)
            table += '_api_calls'

        sql = 'SELECT count FROM ' + table + ' WHERE call_date=DATE(NOW())'

        (rowcount,rows) = self.qs.execute(sql)
        if self.qs.status != 0:
            if self.notify_error:
                self.qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,self.qs.emessage))
            return 'error'

        if rowcount == 0:
           self.logger.info('There are %i API calls for %s for today' % (0,table))
           return 0
        else:
           self.logger.info('There are %s API calls for %s for today' % (rows[0][0],table))
           return rows[0][0]


    def add_api_calls(self,table,count,error=None):
        """
        Add the count of API calls or errors for today
        """

        self.logger.info('Updating API calls/errors for today for %s with %i additional call/error(s)' % (table,count))

        # Counting errors
        if error == 1:
            table += '_api_errors'
        # Counting API calls
        else:
            table += '_api_calls'

        # Either add a new row for this date or update an existing date
        sql  = 'INSERT INTO ' + table + ' (call_date,count)'
        sql += 'VALUES (DATE(NOW()),%s)'
        sql += 'ON DUPLICATE KEY UPDATE count = count + %s'

        # Convert the count int to a string for string interpolation
        count = str(count)

        (rowcount,rows) = self.qs.execute(sql,(count,count))
        if self.qs.status != 0:
            if self.notify_error: 
                self.qm.send('Error','Error executing sql statement:\n%s\n\nERROR:\n%s' % (sql,self.qs.emessage))
            return 'error'

        return rowcount


    def terminate(self):
        """
        Exit program execution, in error
        """

        if self.notify_error:
            self.qm.send('Error','Terminating program execution - check Quinico log for details')

        self.logger.error('Terminating program execution - check Quinico log for details')

        # Disconnect from the DB server
        self.qs.close()
        exit(2)


    def get_date(self,subtract):
        """
        Return a date, minus a certain amount of days
        formatted as %Y-%m-%d
        """

        d = datetime.datetime.today() - datetime.timedelta(days=subtract)
        formatted = d.strftime("%Y-%m-%d")

        return formatted


    def convert_date(self,timezone,d):
        """
        Convert a date given in UTC to a given timezone and format as %Y-%m-%d
        The input format must be: %Y-%m-%dT%H:%M:%S.%f
        """

        d = datetime.datetime.strptime(d, '%Y-%m-%dT%H:%M:%S.%f')

        # The input timezone, which is expected to be UTC
        tz = pytz.timezone('Etc/UTC')

        # Localize the naive time (time w/o timezone) to UTC and then set to the local timezone
        formatted = tz.localize(d).astimezone(pytz.timezone(timezone)).strftime("%Y-%m-%d")

        return formatted


    def convert_date_utc(self,d,timezone):
        """
        Convert a date given in the local timezone to UTC 
        """

        # The input timezone
        tz = pytz.timezone(timezone)

        # Localize the naive time (time w/o timezone) to the local timezone and then convert to UTC
        converted = tz.localize(d).astimezone(pytz.timezone('Etc/UTC'))

        return converted


    def pause(self,pause_time):
        """
        Sleep a number of seconds
        """

        self.logger.info('sleeping %s seconds' % pause_time)
        time.sleep(pause_time)



    def http_request1(self,api,url,count=None):
        """
        Make a web query with urllib
        """

        self.logger.info('requesting URL:%s' % url)

        # Count the API call, if requested to do so
        if count:
            self.add_api_calls(api,1)

        try:
            request = urllib.urlopen(url)
        except Exception as e:
            # Count the error
            self.add_api_calls(api,1,1)

            if self.notify_error:
                self.qm.send('Error','Error encountered requesting url:%s\n%s' % (url,e))

            self.logger.error('Error encountered requesting url (%s):%s' % (url,e))

            return

        response = request.read()
        request.close()

        # Do some checking on the request
        if request.getcode() != 200:
            # Count the error (assume anything other than 200 is an error)
            self.add_api_calls(api,1,1)

            if self.notify_error:
                self.qm.send('Error','bad response code (%s) accessing url:%s with response:%s' % (request.getcode(),url,response))
            self.logger.error('bad response code (%s) accessing url:%s with response:%s' % (request.getcode(),url,response))
            return
        else:
            self.logger.debug('response code: %s' % request.getcode())

        return response


    def http_request2(self,api,url,headers=None,csv=None,count=None):
        """
        Make a web query with urllib2
        """

        self.logger.debug('requesting URL:%s' % url)

        # Count the API call, if requested to do so
        if count:
            self.add_api_calls(api,1)

        r = urllib2.Request(url)

        # If there are headers, add them
        if headers:
            for header in headers:
                self.logger.debug('adding header: %s => %s' % (header,headers[header]))
                r.add_header(header,headers[header])

        try:
            request = urllib2.urlopen(r)
        # With urllib2, almost anything is an exception (including most non-200 responses)
        except Exception as e:
            # Count the error
            self.add_api_calls(api,1,1)

            if self.notify_error:
                self.qm.send('Error','Error encountered requesting url:%s\n%s' % (url,e))

            self.logger.error('Error encountered requesting url (%s):%s' % (url,e))

            return

        if csv:
            self.logger.debug('splitting http response on newlines as requested')
            response = request.read().split('\n')
        else:
            response = request.read()

        request.close()
        return response


    def check_pid(self,file):
        """
        Check to see if a PID file is present
        """

        if os.path.exists(file):
            self.logger.info('Found pid file: %s' % file)
            pidfile = open(file, "r")
            pidfile.seek(0)
            pid = pidfile.readline()

            # See if the PID is running
            if os.path.exists('/proc/%s' % pid):
                self.logger.info('%s is still running.  Only one instance is allowed to run.' % pid)
                return True
            else:
                self.logger.info('%s is not running, removing defunct pid file %s' % (pid,file))
                if (self.remove_pid(file)):
                    # Some error occurred removing the pid file
                    return True

                return False
        else:
            self.logger.info('pid file not found')
            return False


    def set_pid(self,file):
        """
        Set a PID file
            - This should only be called if check_pid returns False
        """

        pid = str(os.getpid())
        try:
            f = open(file, 'w')
            f.write(pid)
            f.close()
        except Exception as e:
            self.logger.error('Could not set pid file %s with error %s' % (file,e))
            return True

        return False


    def remove_pid(self,file):
        """
        Remove a PID file
        """

        self.logger.debug('Removing PID file %s' % file)

        try:
            os.unlink(file)
        except Exception as e:
            self.logger.error('Could not unlink /proc/%s with error %s' % (pid,e))
            return True

        return False


    def save_report(self,upload_path,service,raw_data):
        """Save a raw report file to disk"""

        # Directory name
        date_path = datetime.datetime.now().strftime('%Y/%m/%d')

        # Generate a unique filename
        file_name = uuid.uuid4()

        # Save the report to disk
        # Do everything at once to make error handling easier
        try:
            # Create the date directory if its not already there
            if not os.path.exists('%s/%s/%s' % (upload_path,service,date_path)):
                os.makedirs('%s/%s/%s' % (upload_path,service,date_path))

            # Save the file
            report_file = open('%s/%s/%s/%s' % (upload_path,service,date_path,file_name),'w')
            report_file.write(raw_data)
            report_file.close()

            # Return the file name so it can be saved
            return '%s/%s/%s' % (service,date_path,file_name)
        except Exception as e:
            self.logger.error('Error saving report file: %s' % e)
            if self.notify_error:
                self.qm.send('Error','Error saving report file: %s' % e)

            # Return an empty string for this report
            return ''

