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


"""Models for the Quinico Webmaster Application

   Any models that will be displayed in the DJango admin will have unicode
   methods to display them properly in the admin

"""


from django.db import models
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


class Message_Type(models.Model):
    """Message Types"""

    type = models.CharField(max_length=250, unique=True)


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


class Message(models.Model):
    """Messages"""

    date = models.DateField(null=False,blank=False)
    type = models.ForeignKey(Message_Type)

