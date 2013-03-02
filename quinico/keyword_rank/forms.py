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


"""Form and Form Field classes for the Quinico Keyword Rank application

   All fields should be defined first, with forms to follow.  Form fields
   have basic validation rules and DJango takes care of escaping anything
   dangerous automatically.

"""


import csv
import re
import urllib
from django import forms
from quinico.keyword_rank.models import Domain
from quinico.keyword_rank.models import Keyword
from quinico.keyword_rank.models import Test


### VALIDATORS ###


class FormatField(forms.Field):
    """A format field

       Requirements:
          - Not required to be present
          - Only certain values are accepted (csv, db, json, json1, json2)

    """

    def validate(self, value):
        if value and not re.match(r'^(csv|db|db1|db2|json|json1|json2)$', value):
            raise forms.ValidationError('Improperly formatted format:%s' % (value))


class FileField(forms.FileField):
    """A file field

    Requirements:
       - Must not be empty
       - Need other validation to ensure the file is not malicious

    """

    def validate(self, value):
        # Figure out some validation rules
        if value is None:
            raise forms.ValidationError("No file selected!")


### FORMS ###


class KeywordTrendForm(forms.Form):
    """Form for querying SEO Trends"""

    date_from = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    date_to = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    domain = forms.CharField()
    keyword = forms.CharField()
    format = FormatField()


class KeywordDashboardForm(forms.Form):
    """Form for querying the SEO Dashboard"""

    domain = forms.CharField()
    format = FormatField()


class UploadForm(forms.Form):
    """Form for uploading keywords in bulk"""

    domain = forms.CharField()
    file = FileField()

    def save(self):
        domain = self.cleaned_data['domain']
        records = csv.reader(self.cleaned_data['file'])

        # Make sure the domain exists
        d = Domain.objects.filter(domain=domain)

        if not d:
            raise forms.ValidationError('Domain does not exist: %s.  You must add it before uploading keywords' % value)

        for record in records:

            #k_enc = record[0].decode('windows-1252').encode('utf-8')
            #k_enc = record[0].decode('utf-8').encode('utf-8')
            k_enc = record[0]

            k = Keyword.objects.filter(keyword=k_enc)
            if not k:
                # Not there, so add it
                Keyword(keyword=k_enc).save()

            # See if the keyword is assigned to this domain, if not, add it
            k_d = Test.objects.filter(domain__domain=domain,keyword__keyword=k_enc)
            if not k_d:
                # Not sure how to do a subquery in Django so will need 3 queries
                d_id = Domain.objects.filter(domain=domain).values('id')
                k_id = Keyword.objects.filter(keyword=k_enc).values('id')
                Test(domain_id=d_id[0]['id'],keyword_id=k_id[0]['id']).save()
