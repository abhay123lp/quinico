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


"""Models for the Quinico Dashboard Application

   Any models that will be displayed in the DJango admin will have unicode
   methods to display them properly in the admin

"""


from django.db import models
from django.contrib.auth.models import User


class Url(models.Model):
    """Urls that will be imported into the dashboard for the user"""

    url = models.CharField(max_length=1000)


class Url_Subscription(models.Model):
    """Urls that users are subscribed to"""

    user = models.ForeignKey(User)
    url = models.ForeignKey(Url)


class Subscription(models.Model):
    """Category subscriptions for the user (e.g. SEO or Keyword Rank)"""

    user = models.ForeignKey(User, unique=True)
    keywords = models.BooleanField()
    pagespeed = models.BooleanField()
    webpagetest = models.BooleanField()
    seo = models.BooleanField()
    webmaster = models.BooleanField()


class Dash_Settings(models.Model):
    """Dashboard Settings"""

    user = models.ForeignKey(User, unique=True)
    slots = models.CharField(max_length=3)
    frequency = models.IntegerField(max_length=4)
    width = models.IntegerField(max_length=4)
    height = models.IntegerField(max_length=4)
    font = models.IntegerField(max_length=2)


