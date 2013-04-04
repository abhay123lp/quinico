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


"""Models for the Quinico Keyword Rank Application

   Any models that will be displayed in the DJango admin will have unicode
   methods to display them properly in the admin

"""

from django.db import models
from django.utils.encoding import force_unicode


class Domain(models.Model):
    """Domains that will be tested"""

    domain = models.CharField(max_length=200)
    gl = models.CharField(max_length=25)
    googlehost = models.CharField(max_length=25)

    class Meta:
        unique_together = ['domain','gl','googlehost']

    # Represent the object as unicode
    def __unicode__(self):
        return u'%s | %s | %s' % (self.domain,self.gl,self.googlehost)


class Keyword(models.Model):
    """Keywords that will be tested"""

    keyword = models.CharField(max_length=200, unique=True)

    # Represent the object as unicode
    def __unicode__(self):
        # We need to force unicode b/c the table is utf8_bin
        return force_unicode(self.keyword)
   

class Test(models.Model):
    """Domains and Keywords that will be tested"""

    domain = models.ForeignKey(Domain)
    keyword = models.ForeignKey(Keyword)

    class Meta:
        unique_together = ['domain','keyword']

    # Represent the object as unicode
    def __unicode__(self):
        return u'%s %s' % (self.domain,self.keyword)

class API_Calls(models.Model):
    """Count of Google Search API calls"""

    call_date = models.DateField(null=False,blank=False,unique=True)
    count = models.IntegerField(max_length=11)


class API_Errors(models.Model):
    """Count of Google Search API errors"""

    call_date = models.DateField(null=False,blank=False,unique=True)
    count = models.IntegerField(max_length=11)


class Url(models.Model):
    """Urls that accompany the rank"""

    url = models.CharField(max_length=1000)


class Rank(models.Model):
    """Keyword ranks"""

    date = models.DateField(null=False,blank=False)
    domain = models.ForeignKey(Domain)
    keyword = models.ForeignKey(Keyword)
    url = models.ForeignKey(Url)
    rank = models.IntegerField(max_length=11)


class Top_Ten(models.Model):
    """Top 10 ranks for each keyword"""

    date = models.DateField(null=False,blank=False)
    domain = models.ForeignKey(Domain)
    keyword = models.ForeignKey(Keyword)
    url = models.ForeignKey(Url)
    rank = models.IntegerField(max_length=11)
