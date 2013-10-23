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


"""DJango admin configuration for the Quinico Webmaster Application

   Any models that need to be manipulated in the DJango web admin pages
   will need specific configurations listed below (this is not required).
   They will also need to be registered with the admin

"""


from quinico.webmaster.models import Domain, Message_Status, Message_Pattern
from django.contrib import admin


class DomainAdmin(admin.ModelAdmin):
    """Domain admin class for manipulating domains"""

    fieldsets = [
       ('Domain Name',{'fields':['domain']})
    ]


class Message_StatusAdmin(admin.ModelAdmin):
    """Domain admin class for manipulating message statuses"""

    fieldsets = [
       ('Message Status',{'fields':['status']})
    ]


class Message_PatternAdmin(admin.ModelAdmin):
    """Domain admin class for manipulating message patterns"""

    fieldsets = [
       ('Message Pattern',{'fields':['domain','pattern','user']})
    ]

    list_display = ('domain','pattern','user')


# Register the classes with the admin
admin.site.register(Domain,DomainAdmin)
admin.site.register(Message_Status,Message_StatusAdmin)
admin.site.register(Message_Pattern,Message_PatternAdmin)
