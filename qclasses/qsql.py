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


"""SQL connection management class for Quinico

   Optional:
    - Logging is optional - provide a properly configured instance of
      a logger if desired.
"""


import MySQLdb


class sql:

    Name = "sql"


    def __init__(self, host, username, password, database, logger=None):
        """
        Constructor
        """

        self.host = host
        self.username = username
        self.password = password
        self.database = database
        self.logger = logger
        self.status = 0
        self.emessage = ''

        if not self.logger is None:
            self.logger.info('Connecting to sql server: %s, database: %s' % (host,database))

        try:
            # Connect
            self.db = MySQLdb.connect(host=host,user=username,passwd=password,db=database,charset='utf8',use_unicode=True)

            # Commit everything without needing to specify it
            self.db.autocommit(True)
        except MySQLdb.Error as e:
           if not self.logger is None:
               self.logger.error('Error connecting to MySQL: %s' % e)
               self.status = 1
               self.emessage = e
               return

        # Prepare the cursor
        self.cursor = self.db.cursor()

        # See if we are working
        if not self.logger is None:
            self.logger.debug('MySQL Status: %s' % self.db.stat())


    def execute(self,sql,tup=None):
        """
        Execute SQL
        """

        # Reset status to normal
        self.status = 0
        self.emessage = ''

        if not self.logger is None:
           self.logger.debug('Executing sql: %s' % sql)

        try:
            if tup is None:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql,tup)
        except MySQLdb.Error as e:
           if not self.logger is None:
               self.logger.error('Error executing SQL: %s' % e)
               self.status = 1
               self.emessage = e
               return (0,[])
        else:
            # How many rows affected
            if not self.logger is None:
                self.logger.debug('Rows affected by SQL: %i' % self.cursor.rowcount)

            rowcount = self.cursor.rowcount
            rows = self.cursor.fetchall()
        
            return (rowcount,rows)


    def close_cursor(self):
        """
        Close the MySQL cursor
        """

        # Close the cursor
        self.cursor.close()
        self.db.close()


    def close(self):
        """
        Close MySQL connection
        """

        # Reset status to normal
        self.status = 0
        self.emessage = ''

        if not self.logger is None:
            self.logger.info('Closing MySQL connection')

        try:
            self.cursor.close()
            self.db.close()
        except MySQLdb.Error as e:
           if not self.logger is None:
               self.logger.error('Error closing connection: %s' % e)
