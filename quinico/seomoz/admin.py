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


"""DJango admin configuration for the Quinico SEOMoz Application

   Any models that need to be manipulated in the DJango web admin pages
   will need specific configurations listed below (this is not required).
   They will also need to be registered with the admin

"""


from quinico.seomoz.models import Url
from quinico.seomoz.models import Competitor
from quinico.seomoz.models import Description
from django.contrib import admin


class UrlAdmin(admin.ModelAdmin):
    """Url admin class for manipulating urls"""

    fieldsets = [
       ('Url Name',{'fields':['url']})
    ]


class CompetitorAdmin(admin.ModelAdmin):
    """Competitor admin class for manipulating competitors"""

    fieldsets = [
       ('Competitor Url',{'fields':['url','comp']})
    ]

    list_display = ('url','comp')


class DescriptionAdmin(admin.ModelAdmin):
    """Description admin class for manipulating SEO metric descriptions"""

    fieldsets = [
       ('Metric Description',{'fields':['metric','column_description','full_description','represent']})
    ]

    list_display = ('metric','column_description','full_description','represent')


# Register the classes with the admin
admin.site.register(Url,UrlAdmin)
admin.site.register(Competitor,CompetitorAdmin)
admin.site.register(Description,DescriptionAdmin)
