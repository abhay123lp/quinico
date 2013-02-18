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


"""Form and Form Field classes for the Quinico Pagespeed application

   All fields should be defined first, with forms to follow.  Form fields
   have basic validation rules and DJango takes care of escaping anything
   dangerous automatically.

"""


import re
from django import forms


class FormatField(forms.Field):
    """A format field

       Requirements:
          - Only certain values are accepted (csv, db, json)

    """

    def validate(self, value):
        if value and not re.match(r'^(csv|db|json)$', value):
            raise forms.ValidationError('Improperly formatted format:%s' % (value))


class StrategyField(forms.Field):
    """A strategy field

    Requirements:
       - Must not be empty
       - Must only be mobile or desktop

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('No strategy selected')
        if not re.match(r'^(mobile|desktop)$', value):
            raise forms.ValidationError('Improperly formatted strategy:%s' % (value))


### FORMS ###


class PagespeedTrendForm(forms.Form):
    """Form for querying Pagespeed trends"""

    date_from = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    date_to = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    domain = forms.CharField()
    url = forms.CharField()
    metric = forms.CharField()
    strategy = StrategyField()
    format = FormatField()


class PagespeedBreakdownForm(forms.Form):
    """Form for querying Pagespeed page breakdown"""

    date = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    domain = forms.CharField()
    url = forms.CharField()
    strategy = StrategyField()
    format = FormatField()


class PagespeedHistoryForm(forms.Form):
    """Form for querying Pagespeed history"""

    date_from = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    date_to = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    domain = forms.CharField()
    url = forms.CharField()
    strategy = StrategyField()
    format = FormatField()


class PagespeedReportForm(forms.Form):
    """Form for querying the entire Pagespeed report"""

    id = forms.IntegerField(min_value=1)
