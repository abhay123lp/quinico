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


"""Mail sending class for Quinico

   Requirements:
    1. A properly configured SMTP host
    2. Valid sender and recipient addresses

   Optional:
    1. Logging is optional - provide a properly configured instance of
       a logger if desired.
"""


import inspect
import smtplib
import socket
import time


class notify:

    Name = "notify"


    def __init__(self, server, sender, recipient, logger=None):
        """Constructor"""

        self.server = server
        self.sender = sender
        self.recipient = recipient
        self.logger = logger


    def send(self,subject,message):
        """Send an email message"""

        # Obtain the hostname
        if socket.gethostname().find('.')>=0:
            hostname=socket.gethostname()
        else:
            hostname=socket.gethostbyaddr(socket.gethostname())[0]

        # Obtain the localtime
        localtime = time.asctime( time.localtime(time.time()) )

        # Obtain the calling job
        job = inspect.stack()[-1][1]

        # Construct the message
        m = 'To: %s\nFrom: %s\nSubject: Quinico - %s\nQuinico Server:%s\nLocal Time:%s\nJob:%s\n\n%s' % (self.recipient,
											                 self.sender,
											                 subject,
                                                                                                         hostname,
                                                                                                         localtime,
                                                                                                         job,
                                                                                                         message)

        try:
            smtpObj = smtplib.SMTP(self.server)
            smtpObj.sendmail(self.sender, self.recipient, m)
            if not self.logger is None:
                self.logger.info('Successfully sent email')
        except Exception as e:
            if not self.logger is None:
                self.logger.error('Unable to send email:%s' % e)
