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


"""Models for the Quinico Pagespeed Application

   Any models that will be displayed in the DJango admin will have unicode
   methods to display them properly in the admin

"""


from django.db import models


class Config(models.Model):
    """Configuration Parameters
    
    The config_value and description need to be sufficiently large to accommodate
    enough help text to be useful
    """

    config_name = models.CharField(max_length=50, unique=True)
    friendly_name = models.CharField(max_length=50, unique=True)
    config_value = models.CharField(max_length=800,blank=True)
    description = models.CharField(max_length=500,blank=True)
    display = models.CharField(max_length=8,blank=False)

    # Represent the object as unicode
    def __unicode__(self):
        return self.config_name


class Help(models.Model):
    """Help Documents"""

    help_name = models.CharField(max_length=100, unique=True)
    help_value = models.CharField(max_length=1500)

    # Represent the objects as unicode
    def __unicode__(self):
        return u'%s %s' % (self.help_name,self.help_value)


class Data_Job(models.Model):
    """Data Jobs"""

    job_name = models.CharField(max_length=25, unique=True)
    job_status = models.BooleanField(default=False)
    job_hour = models.CharField(max_length=50,blank=True)
    job_minute = models.CharField(max_length=25,blank=True)

