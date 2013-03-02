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


"""DJango admin configuration for the Quinico Webpagetest Application

   Any models that need to be manipulated in the DJango web admin pages
   will need specific configurations listed below (this is not required).
   They will also need to be registered with the admin

"""


from quinico.webpagetest.models import Domain
from quinico.webpagetest.models import Url
from quinico.webpagetest.models import Location
from quinico.webpagetest.models import Test
from django.contrib import admin


class DomainAdmin(admin.ModelAdmin):
    """Domain admin class for manipulating domains"""

    fieldsets = [
       ('Domain Name',{'fields':['domain']})
    ]


class UrlAdmin(admin.ModelAdmin):
    """Url admin class for manipulating urls"""

    fieldsets = [
       ('Urls',{'fields':['url']}),
    ]


class LocationAdmin(admin.ModelAdmin):
    """Location admin class for manipulating locations"""

    fieldsets = [
       ('Locations',{'fields':['location']}),
    ]


class TestAdmin(admin.ModelAdmin):
    """Test admin class for manipulating test"""

    fieldsets = [
       ('Tests',{'fields':['domain','url','location']}),
    ]

    list_display = ('domain','url','location')


# Register the classes with the admin
admin.site.register(Domain,DomainAdmin)
admin.site.register(Url,UrlAdmin)
admin.site.register(Location,LocationAdmin)
admin.site.register(Test,TestAdmin)
