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


"""Form and Form Field classes for the Quinico SEOMoz application

   All fields should be defined first, with forms to follow.  Form fields
   have basic validation rules and DJango takes care of escaping anything
   dangerous automatically.

"""


import re
from django import forms


### VALIDATORS ###

class FormatField(forms.Field):
    """A format field

       Requirements:
          - Not required to be present
          - Only certain values are accepted (csv, db, json)

    """

    def validate(self, value):
        if value and not re.match(r'^(csv|db|db1|db2|json|json1|json2)$', value):
            raise forms.ValidationError('Improperly formatted format:%s' % (value))


### FORMS ###


class SEOTrendForm(forms.Form):
    """Form for querying SEO Trends"""

    date_from = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    date_to = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    url = forms.CharField()
    metric = forms.CharField()
    format = FormatField()


class SEODashboardForm(forms.Form):
    """Form for creating the SEO Dashboard"""

    date = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    url = forms.CharField()
    format = FormatField()
