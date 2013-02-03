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


class DateField(forms.Field):
    """A date field

       Requirements:
          - Must be in SQL format (yyyy-mm-dd)

    """

    def validate(self, value):
        if value and not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            raise forms.ValidationError('Improperly formatted date:%s' % (value))


class FormatField(forms.Field):
    """A format field

       Requirements:
          - Only certain values are accepted (csv, db, json)

    """

    def validate(self, value):
        if value and not re.match(r'^(csv|db|json)$', value):
            raise forms.ValidationError('Improperly formatted format:%s' % (value))


class DomainField(forms.Field):
    """A domain field

    Requirements:
       - Must not be empty
       - Must contain only alpha-numeric and '\-.'

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('No domain selected')
        if not re.match(r'^[0-9a-zA-Z/\-\.]+$', value):
            raise forms.ValidationError('Improperly formatted domain:%s' % (value))


class UrlField(forms.Field):
    """A url field

    Requirements:
       - Must not be empty
       - Must contain only alpha-numeric and '\-%.'

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('No url selected')
        if not re.match(r'^[0-9a-zA-Z/\-%\.]+$', value):
            raise forms.ValidationError('Improperly formatted url:%s' % (value))


class MetricField(forms.Field):
    """A metric field

    Requirements:
       - Must not be empty
       - Must contain only alpha-numeric and _

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('No metric selected')
        if not re.match(r'^[A-Za-z_]+$', value):
            raise forms.ValidationError('Improperly formatted metric:%s' % (value))


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


class IdField(forms.Field):
    """An ID field

    Requirements:
       - Must not be empty
       - Must contain only digits

    """

    def validate(self, value):
        if value is None or value == '': 
            raise forms.ValidationError('No id selected')
        if not re.match(r'^\d+$', value):
            raise forms.ValidationError('Improperly formatted id:%s' % (value))


### FORMS ###


class PagespeedTrendForm(forms.Form):
    """Form for querying Pagespeed trends"""

    date_from = DateField()
    date_to = DateField()
    domain = DomainField()
    url = UrlField()
    metric = MetricField()
    strategy = StrategyField()
    format = FormatField()


class PagespeedBreakdownForm(forms.Form):
    """Form for querying Pagespeed page breakdown"""

    date = DateField()
    domain = DomainField()
    url = UrlField()
    strategy = StrategyField()
    format = FormatField()


class PagespeedHistoryForm(forms.Form):
    """Form for querying Pagespeed history"""

    date_from = DateField()
    date_to = DateField()
    domain = DomainField()
    url = UrlField()
    strategy = StrategyField()
    format = FormatField()


class PagespeedReportForm(forms.Form):
    """Form for querying the entire Pagespeed report"""

    id = IdField()
