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


"""Models for the Quinico Webmaster Application

   Any models that will be displayed in the DJango admin will have unicode
   methods to display them properly in the admin

"""


from django.db import models
from django.contrib.auth.models import User
from quinico.keyword_rank.models import Keyword


class Domain(models.Model):
    """Domains that will be checked"""

    domain = models.CharField(max_length=200, unique=True)

    # Represent the object as unicode
    def __unicode__(self):
        return self.domain


class API_Calls(models.Model):
    """Count of Webmaster API calls"""

    call_date = models.DateField(null=False,blank=False,unique=True)
    count = models.IntegerField(max_length=11)


class API_Errors(models.Model):
    """Count of Webmaster API errors"""

    call_date = models.DateField(null=False,blank=False,unique=True)
    count = models.IntegerField(max_length=11)


class Crawl_Error_Type(models.Model):
    """Crawl Error Types"""

    type = models.CharField(max_length=50, unique=True)


class Crawl_Error(models.Model):
    """Crawl Errors"""

    date = models.DateField(null=False,blank=False)
    domain = models.ForeignKey(Domain)
    type = models.ForeignKey(Crawl_Error_Type)
    count = models.IntegerField(max_length=11)


class Top_Search_Queries(models.Model):
    """Top Search Queries"""

    date = models.DateField(null=False,blank=False)
    domain = models.ForeignKey(Domain)
    keyword = models.ForeignKey(Keyword)
    impressions = models.CharField(max_length=11)
    clicks = models.CharField(max_length=11)


class Message_Status(models.Model):
    """Webmaster Message Status"""

    status = models.CharField(max_length=11)

    # Represent the object as unicode
    def __unicode__(self):
        return self.status


class Messages(models.Model):
    """Webmaster Messages"""

    date = models.DateTimeField(null=False, blank=False)
    date_discovered = models.DateTimeField(null=False, blank=False)
    subject = models.CharField(max_length=500, null=False, blank=False)
    body = models.CharField(max_length=8000, null=False, blank=False)
    status = models.ForeignKey(Message_Status, null=True, blank=True)
    assignee = models.ForeignKey(User, null=True, blank=True)


class Message_Update(models.Model):
    """Webmaster Message Updates"""

    date = models.DateTimeField(null=False,blank=False,auto_now=True)
    message = models.ForeignKey(Messages)
    user = models.ForeignKey(User)
    update = models.CharField(max_length=2000)


class Message_Pattern(models.Model):
    """Webmaster Message Patterns that will trigger actions"""

    pattern = models.CharField(null=False, blank=False, max_length=250, unique=True)
    user = models.ForeignKey(User)    
