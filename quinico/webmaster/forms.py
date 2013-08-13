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


"""Form and Form Field classes for the Quinico Webmaster application

   All fields should be defined first, with forms to follow.  Form fields
   have basic validation rules and DJango takes care of escaping anything
   dangerous automatically.

"""


import re
from django import forms


class FormatField(forms.Field):
    """A format field

       Requirements:
          - Not required to be present
          - Only certain values are accepted (csv, db, xml, json)

    """

    def validate(self, value):
        if value and not re.match(r'^(csv|db|db1|db2|json|json1|json2)$', value):
            raise forms.ValidationError('Improperly formatted format:%s' % (value))


### FORMS ###


class QueriesForm(forms.Form):
    """Form for querying Google search query trends"""

    date_from =  forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    date_to =  forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    domain = forms.CharField()
    keyword = forms.CharField()
    format = FormatField()
    width = forms.IntegerField(required=False)
    height = forms.IntegerField(required=False)
    step = forms.IntegerField(required=False)

    # Override the form clean method - there is some special logic to validate 

    def clean(self):
        cleaned_data = super(QueriesForm, self).clean()
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')

        if width and not height:
            self._errors["height"] = self.error_class(['You must define a width and height'])
        
        if height and not width:
            self._errors["width"] = self.error_class(['You must define a width and height'])
        
        # Return the full collection of cleaned data
        return cleaned_data


class CrawlErrorTrendForm(forms.Form):
    """Form for querying Google crawl error trends"""

    date_from = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    date_to = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    domain = forms.CharField()
    error_id = forms.IntegerField()
    format = FormatField()
    width = forms.IntegerField(required=False)
    height = forms.IntegerField(required=False)
    step = forms.IntegerField(required=False)

    # Override the form clean method - there is some special logic to validate 

    def clean(self):
        cleaned_data = super(CrawlErrorTrendForm, self).clean()
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')

        if width and not height:
            self._errors["height"] = self.error_class(['You must define a width and height'])
        
        if height and not width:
            self._errors["width"] = self.error_class(['You must define a width and height'])
        
        # Return the full collection of cleaned data
        return cleaned_data


class TotalCrawlErrorTrendForm(forms.Form):
    """Form for querying Total Google crawl error trends"""

    date_from = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    date_to = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    domain = forms.CharField()
    format = FormatField()
    width = forms.IntegerField(required=False)
    height = forms.IntegerField(required=False)
    step = forms.IntegerField(required=False)

    # Override the form clean method - there is some special logic to validate 

    def clean(self):
        cleaned_data = super(TotalCrawlErrorTrendForm, self).clean()
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')

        if width and not height:
            self._errors["height"] = self.error_class(['You must define a width and height'])
        
        if height and not width:
            self._errors["width"] = self.error_class(['You must define a width and height'])
        
        # Return the full collection of cleaned data
        return cleaned_data


class CrawlErrorSummaryForm(forms.Form):
    """Form for querying crawl errors for a single day"""

    date = forms.DateField(required=False,input_formats=['%Y-%m-%d'])
    domain = forms.CharField()


class MessageDetailForm(forms.Form):
    """Form for displaying details of a Google Webmaster message"""

    id = forms.IntegerField(required=True)


class MessageUpdateForm(forms.Form):
    """Form for updating details of a Google Webmaster message"""

    id = forms.IntegerField(required=True)
    update = forms.CharField(required=True)
    status = forms.IntegerField(required=True)


class MessageForm(forms.Form):
    """Form for querying messages"""

    page = forms.IntegerField(required=False)
    filter = forms.IntegerField(required=False)
    format = FormatField() 
    color = forms.CharField(required=False)
    size = forms.IntegerField(required=False)  


class MessageDeleteForm(forms.Form):
    """Form for deleting messages"""

    id = forms.IntegerField(required=True)
   