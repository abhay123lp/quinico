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


"""DJango admin configuration for the Quinico Main Application

   Any models that need to be manipulated in the DJango web admin pages
   will need specific configurations listed below (this is not required).
   They will also need to be registered with the admin

"""


from quinico.main.models import Help
from quinico.main.forms import HelpAdminForm
from django.contrib import admin


class HelpAdmin(admin.ModelAdmin):
    """Help admin class for help blurbs"""
    form = HelpAdminForm

    fieldsets = [
       ('Help Blurb',{'fields':['help_name','help_value']})
    ]

    list_display = ('help_name','help_value')


# Register the classes with the admin
admin.site.register(Help,HelpAdmin)
