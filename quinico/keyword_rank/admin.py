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


"""DJango admin configuration for the Quinico Keyword Rank Application

   Any models that need to be manipulated in the DJango web admin pages
   will need specific configurations listed below (this is not required).
   They will also need to be registered with the admin

"""


from quinico.keyword_rank.models import Keyword
from quinico.keyword_rank.models import Domain
from quinico.keyword_rank.models import Test
from django.contrib import admin


class DomainAdmin(admin.ModelAdmin):
    """Domain admin class for manipulating domains"""

    fieldsets = [
       ('Domain Name',{'fields':['domain','gl','googlehost']})
    ]

    list_display = ('domain','gl','googlehost')


class KeywordAdmin(admin.ModelAdmin):
    """Keyword admin class for manipulating keywords"""

    fieldsets = [
       ('Keywords',{'fields':['keyword']}),
    ]


class TestAdmin(admin.ModelAdmin):
    """Test admin class for manipulating keyword tests"""

    fieldsets = [
       ('Tests',{'fields':['domain','keyword']}),
    ]

    list_display = ('domain','keyword')


# Register the classes with the admin
admin.site.register(Domain,DomainAdmin)
admin.site.register(Keyword,KeywordAdmin)
admin.site.register(Test,TestAdmin)
