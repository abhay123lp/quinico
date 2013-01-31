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


"""Form and Form Field classes for the Quinico Webpagetest application

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
        if value and not re.match(r'^(csv|db|db1|db2|json)$', value):
            raise forms.ValidationError('Improperly formatted format:%s' % (value))


class MetricField(forms.Field):
    """A metric field

    Requirements:
       - Must not be empty
       - Must contain only alpha-numeric

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('No metric selected')
        if not re.match(r'^[A-Za-z_]+$', value):
            raise forms.ValidationError('Improperly formatted metric:%s' % (value))


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


class WebpagetestTrendForm(forms.Form):
    """Form for querying Webpagetest Trends"""

    date_from = DateField()
    date_to = DateField()
    format = FormatField()
    metric = MetricField()
    test_id = IdField()


class WebpagetestHistoryForm(forms.Form):
    """Form for querying Webpagetest history"""

    date_from = DateField()
    date_to = DateField()
    test_id = IdField()
    format = FormatField()

