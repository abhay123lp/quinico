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


"""Form and Form Field classes for the Quinico Main Application

   All fields should be defined first, with forms to follow.  Form fields
   have basic validation rules and DJango takes care of escaping anything
   dangerous automatically.

"""


import os
import re
from django import forms
from quinico.main.models import Help


### VALIDATORS ###

class MultipleHourField(forms.Field):
    """A numeric ID field

       Requirements:
          - Must not be empty
          - Must be a number from 0 - 23
          - Multiple numbers allowed, separated by commas

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('Empty values not allowed')
        if re.match(r'^(\d{1,2},?)+$', value):
            nums = value.split(',')
            
            # Don't allow the same hour more than once
            # and make sure its in a valid range
            nums_uniq = {}
            for num in nums:
                if int(num) in nums_uniq:
                    raise forms.ValidationError('Number entered more than once: %s' % num)

                if not 0 <= int(num) <= 23:
                    raise forms.ValidationError('Not in valid range: %s' % value)

                # Add number to the uniq dict
                nums_uniq[int(num)] = ''
        else:
            raise forms.ValidationError('Not a properly formatted number: %s' % value)


class HourField(forms.Field):
    """A numeric ID field

       Requirements:
          - Must not be empty
          - Must be a number from 0 - 23

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('Empty values not allowed')
        if re.match(r'^\d{1,2}$', value):
            if not 0 <= int(value) <= 23:
                raise forms.ValidationError('Not in valid range: %s' % value)
        else:
            raise forms.ValidationError('Not a properly formatted number: %s' % value)


class MinuteField(forms.Field):
    """A numeric ID field

       Requirements:
          - Must not be empty
          - Must be a number from 0 - 59

    """

    def validate(self, value):
        if value is None or value == '':
            raise forms.ValidationError('Empty values not allowed')
        if re.match(r'^\d{1,2}$', value):
            if not 0 <= int(value) <= 59:
                raise forms.ValidationError('Not in valid range: %s' % value)
        else:
            raise forms.ValidationError('Not a properly formatted number: %s' % value)


class SEOMozAccountField(forms.Field):
    """SEOMoz Account Type Field

       Requirements:
          - Must be either free or paid

    """

    def validate(self, value):
        if value is None or value == '':
            pass
        elif not re.match(r'^free|paid$', value):
            raise forms.ValidationError('Not a valid entry: %s' % value)


class DashboardSlotsField(forms.Field):
    """Dashboard Slots Field

       Requirements:
          - Must be two integers separated by an x

    """

    def validate(self, value):
        if value is None or value == '':
            pass
        elif not re.match(r'^\d+x\d+$', value):
            raise forms.ValidationError('Not a valid entry: %s' % value)


class LocaleField(forms.Field):
    """Locale Field

       Requirements:
          - Can be only lowercase, uppercase and _ characters

    """

    def validate(self, value):
        if value is None or value == '':
            pass
        elif not re.match(r'^[a-zA-Z_]+$', value):
            raise forms.ValidationError('Not a valid entry: %s' % value)


class PathField(forms.Field):
    """Unix Path Field

       Requirements:
          - Can be only a valid Unix path

    """

    def validate(self, value):
        if value is None or value == '':
            pass
        elif not os.path.exists(value):
            raise forms.ValidationError('Path does not exist: %s' % value)


### FORMS ###


class JobsForm(forms.Form):
    """Form for updating data collection jobs"""

    pagespeed_hour = MultipleHourField()
    pagespeed_minute = MinuteField()
    webmaster_hour = HourField()
    webmaster_minute = MinuteField()
    seomoz_hour = HourField()
    seomoz_minute = MinuteField()
    keyword_rank_hour = HourField()
    keyword_rank_minute = MinuteField()
    webpagetest_hour = MultipleHourField()
    webpagetest_minute = MinuteField()

class ConfigForm(forms.Form):
    """Form for updating configs"""

    google_key = forms.CharField(required=False)
    google_se_id = forms.CharField(required=False)
    google_wm_username = forms.CharField(required=False)
    google_wm_password = forms.CharField(required=False)
    max_google_api_calls = forms.IntegerField(required=False)
    max_keyword_results = forms.IntegerField(required=False)
    seomoz_access_id = forms.CharField(required=False)
    seomoz_account_type = SEOMozAccountField()
    seomoz_secret_key = forms.CharField(required=False)
    smtp_notify_data_start = forms.IntegerField(required=False)
    smtp_notify_seomoz_new = forms.IntegerField(required=False)
    wpt_attempts = forms.IntegerField(required=False)
    wpt_key = forms.CharField(required=False)
    wpt_wait = forms.IntegerField(required=False)
    wpt_threads = forms.IntegerField(required=False, min_value=1, max_value=100)
    dashboard_refresh = forms.IntegerField(required=False)
    dashboard_slots = DashboardSlotsField(required=False)
    dashboard_width = forms.IntegerField(required=False)
    dashboard_height = forms.IntegerField(required=False)
    dashboard_font = forms.IntegerField(required=False)
    dashboard_frequency = forms.IntegerField(required=False)
    alert = forms.CharField(required=False)
    pagespeed_locale = LocaleField()
    pagespeed_upload = PathField()
    pagespeed_threads = forms.IntegerField(required=False, min_value=1, max_value=100)
    disable_pagespeed_reports = forms.IntegerField(required=False)
    disable_keyword_rank_reports = forms.IntegerField(required=False)
    disable_webmaster_reports = forms.IntegerField(required=False)
    disable_webpagetest_reports = forms.IntegerField(required=False)
    disable_seomoz_reports = forms.IntegerField(required=False)


class HelpAdminForm(forms.ModelForm):
    """Form for updating help documents

    """

    help_value = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Help



