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


"""DJango admin configuration for the Quinico Pagespeed Application

   Any models that need to be manipulated in the DJango web admin pages
   will need specific configurations listed below (this is not required).
   They will also need to be registered with the admin

"""


from quinico.pagespeed.models import Domain
from quinico.pagespeed.models import Url
from quinico.pagespeed.models import Test
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


class TestAdmin(admin.ModelAdmin):
    """Test admin class for manipulating pagespeed tests"""

    fieldsets = [
       ('Tests',{'fields':['domain','url']}),
    ]

    list_display = ('domain','url')


# Register the classes with the admin
admin.site.register(Domain,DomainAdmin)
admin.site.register(Url,UrlAdmin)
admin.site.register(Test,TestAdmin)
