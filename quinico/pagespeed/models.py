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


"""Models for the Quinico Pagespeed Application

   Any models that will be displayed in the DJango admin will have unicode
   methods to display them properly in the admin

"""


from django.db import models


class Domain(models.Model):
    """Domains that will be tested"""

    domain = models.CharField(max_length=200, unique=True)

    # Represent the object as unicode
    def __unicode__(self):
        return self.domain


class Url(models.Model):
    """URLs that will be tested (for any domain) """

    url = models.CharField(max_length=1000, unique=True)

    # Represent the object as unicode
    def __unicode__(self):
        return self.url


class Test(models.Model):
    """Domains and Urls that will be tested """

    domain = models.ForeignKey(Domain)
    url = models.ForeignKey(Url)

    class Meta:
        unique_together = ['domain','url']


class API_Calls(models.Model):
    """Count of Pagespeed API calls"""

    call_date = models.DateField(null=False,blank=False)
    count = models.IntegerField(max_length=11)


class API_Errors(models.Model):
    """Count of Pagespeed API errors"""

    call_date = models.DateField(null=False,blank=False)
    count = models.IntegerField(max_length=11)


class Score(models.Model):
    """Pagespeed Score"""

    date = models.DateField(null=False,blank=False)
    test = models.ForeignKey(Test)
    strategy = models.CharField(max_length=11)
    score = models.IntegerField(max_length=3)
    numberHosts = models.IntegerField(max_length=11)
    numberResources = models.IntegerField(max_length=11)
    numberCssResources = models.IntegerField(max_length=11)
    numberStaticResources = models.IntegerField(max_length=11)
    totalRequestBytes = models.IntegerField(max_length=11)
    textResponseBytes = models.IntegerField(max_length=11)
    cssResponseBytes = models.IntegerField(max_length=11)
    htmlResponseBytes = models.IntegerField(max_length=11)
    imageResponseBytes = models.IntegerField(max_length=11)
    javascriptResponseBytes = models.IntegerField(max_length=11)
    otherResponseBytes = models.IntegerField(max_length=11)

