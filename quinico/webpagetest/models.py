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


"""Models for the Quinico Webpagetest Application

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
    """URLs that will be tested (for any domain)"""

    url = models.CharField(max_length=255, unique=True)

    # Represent the object as unicode
    def __unicode__(self):
        return self.url


class Location(models.Model):
    """Locations that will be used (for any domain and url)"""

    location = models.CharField(max_length=100, unique=True)

    # Represent the object as unicode
    def __unicode__(self):
        return self.location


class Test(models.Model):
    """Domains and Urls that will be tested from locations"""

    domain = models.ForeignKey(Domain)
    url = models.ForeignKey(Url)
    location = models.ForeignKey(Location)

    class Meta:
        unique_together = ['domain','url','location']


class API_Calls(models.Model):
    """Count of Webpagetest API calls"""

    call_date = models.DateField(null=False,blank=False,unique=True)
    count = models.IntegerField(max_length=11)


class API_Errors(models.Model):
    """Count of Webpagetest API errors"""

    call_date = models.DateField(null=False,blank=False,unique=True)
    count = models.IntegerField(max_length=11)


class Score(models.Model):
    """Webpagetest Scores"""

    date = models.DateTimeField(null=False,blank=False)
    test = models.ForeignKey(Test)
    testId = models.CharField(max_length=25)
    viewNumber = models.IntegerField(max_length=1)
    loadTime = models.IntegerField(max_length=5)
    ttfb = models.IntegerField(max_length=5)
    bytesOut = models.IntegerField(max_length=11)
    bytesOutDoc = models.IntegerField(max_length=11)
    bytesIn = models.IntegerField(max_length=11)
    bytesInDoc = models.IntegerField(max_length=11)
    connections = models.IntegerField(max_length=5)
    requests = models.IntegerField(max_length=5)
    requestsDoc = models.IntegerField(max_length=5)
    responses_200 = models.IntegerField(max_length=5)
    responses_404 = models.IntegerField(max_length=5)
    responses_other = models.IntegerField(max_length=5)
    result = models.IntegerField(max_length=3)
    render = models.IntegerField(max_length=5)
    fullyLoaded = models.IntegerField(max_length=5)
    cached = models.IntegerField(max_length=5)
    docTime = models.IntegerField(max_length=5)
    domTime = models.IntegerField(max_length=5)
    score_cache = models.IntegerField(max_length=3)
    score_cdn = models.IntegerField(max_length=3)
    score_gzip = models.IntegerField(max_length=3)
    score_cookies = models.IntegerField(max_length=3)
    score_keep_alive = models.IntegerField(max_length=3)
    score_minify = models.IntegerField(max_length=3)
    score_combine = models.IntegerField(max_length=3)
    score_compress = models.IntegerField(max_length=3)
    score_etags = models.IntegerField(max_length=3)
    gzip_total = models.IntegerField(max_length=11)
    gzip_savings = models.IntegerField(max_length=11)
    minify_total = models.IntegerField(max_length=11)
    minify_savings = models.IntegerField(max_length=11)
    image_total = models.IntegerField(max_length=11)
    image_savings = models.IntegerField(max_length=11)
    aft = models.IntegerField(max_length=5)
    domElements = models.IntegerField(max_length=5)
    test_failed = models.BooleanField(default=False)
    view_failed = models.BooleanField(default=False)
    report = models.CharField(max_length=65)

    class Meta:
        unique_together = ['id','report']
