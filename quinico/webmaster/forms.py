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


"""Form and Form Field classes for the Quinico Webmaster application

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
          - Only certain values are accepted (csv, db, xml, json)

    """

    def validate(self, value):
        if value and not re.match(r'^(csv|db|xml|json)$', value):
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


class KeywordField(forms.Field):
    """A keyword field

    Requirements:
       - Must not be empty
       - Must contain only alpha-numeric and \-%\s'

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('No keyword selected')
        if not re.match(r'^[0-9a-zA-Z/\-%\s\']+$', value):
            raise forms.ValidationError('Improperly formatted keyword:%s' % (value))


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


class QueriesForm(forms.Form):
    """Form for querying Google search query trends"""

    date_from = DateField()
    date_to = DateField()
    domain = DomainField()
    keyword = KeywordField()
    format = FormatField()

class CrawlErrorTrendForm(forms.Form):
    """Form for querying Google crawl error trends"""

    date_from = DateField()
    date_to = DateField()
    domain = DomainField()
    error_id = IdField()
    format = FormatField()

class TotalCrawlErrorTrendForm(forms.Form):
    """Form for querying Total Google crawl error trends"""

    date_from = DateField()
    date_to = DateField()
    domain = DomainField()
    format = FormatField()


class CrawlErrorSummaryForm(forms.Form):
    """Form for querying crawl errors for a single day"""

    date = DateField()
    domain = DomainField()
