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


"""This module contains all of the views for the Quinico Main
   application

"""


import datetime
import logging
import os
import sys
from crontab import CronTab
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from quinico.webmaster.models import API_Errors as webmaster_errors
from quinico.keyword_rank.models import API_Errors as keyword_rank_errors
from quinico.seomoz.models import API_Errors as seomoz_errors
from quinico.pagespeed.models import API_Errors as pagespeed_errors
from quinico.webpagetest.models import API_Errors as webpagetest_errors
from quinico.main.models import Config
from quinico.main.models import Data_Job
from quinico.main.forms import ConfigForm
from quinico.main.forms import JobsForm


# Get an instance of a logger
logger = logging.getLogger(__name__)


def index(request):
    """Default Index Page

    """

    # Obtain the dates to check for errors
    now = datetime.datetime.today()

    # Move back 5 days
    then = datetime.timedelta(days=5)
    then = now - then

    # See if we have any errors for today
    apis = ['webmaster','keyword_rank','seomoz','pagespeed','webpagetest']
    lights = {}

    for api in apis:
        # Convert the api name into the appropriate errors class
        er = getattr(sys.modules[__name__],(api + '_errors'))
        errors = er.objects.filter(call_date=now).values('call_date').annotate(Sum('count')).order_by('-call_date')

        # If no errors today, then check in the last 5 days
        if not errors:
            errors_5 = er.objects.filter(call_date__range=[then,now]).values('call_date').annotate(Sum('count')).order_by('-call_date')

            # If no errors in the last 5 days, set the light to green
            if not errors_5:
                lights[api] = 'green'

            # There were errors in the last 5 days (but not today), so set the light to orange
            else:
                lights[api] = 'orange'
   
        # There was an error today so set the light to red
        else:
            lights[api] = 'red'
    
    # See if there is an alert
    alert = Config.objects.filter(config_name='alert').values('config_value')[0]['config_value']

    # See if we are disabling any reports (just load all configs)
    reports = {}
    reports['disable_pagespeed'] = int(Config.objects.filter(config_name='disable_pagespeed_reports').values('config_value')[0]['config_value'])
    reports['disable_keyword_rank'] = int(Config.objects.filter(config_name='disable_keyword_rank_reports').values('config_value')[0]['config_value'])
    reports['disable_webpagetest'] = int(Config.objects.filter(config_name='disable_webpagetest_reports').values('config_value')[0]['config_value'])
    reports['disable_seomoz'] = int(Config.objects.filter(config_name='disable_seomoz_reports').values('config_value')[0]['config_value'])
    reports['disable_webmaster'] = int(Config.objects.filter(config_name='disable_webmaster_reports').values('config_value')[0]['config_value'])

    # Print the page
    return render_to_response(
       'main/index.html',
       {
          'title':'Quinico | Home',
          'lights':lights,
          'reports':reports,
          'alert':alert
       },
       context_instance=RequestContext(request)
    )


@staff_member_required
def datajobs(request):
    """Manage Data Jobs

    """

    # Quinico location
    app_dir = settings.APP_DIR

    if request.method == 'POST':

        # Check the form elements
        form = JobsForm(request.POST)

        if form.is_valid():

            # Obtain the cleaned data
            pagespeed_hour = form.cleaned_data['pagespeed_hour']
            pagespeed_minute = form.cleaned_data['pagespeed_minute']
            webmaster_hour = form.cleaned_data['webmaster_hour']
            webmaster_minute = form.cleaned_data['webmaster_minute']
            seomoz_hour = form.cleaned_data['seomoz_hour']
            seomoz_minute = form.cleaned_data['seomoz_minute']
            keyword_rank_hour = form.cleaned_data['keyword_rank_hour']
            keyword_rank_minute = form.cleaned_data['keyword_rank_minute']
            webpagetest_hour = form.cleaned_data['webpagetest_hour']
            webpagetest_minute = form.cleaned_data['webpagetest_minute']

            # Access the crontab
            cron = CronTab()
          
            # Remove everything from the crontab - Quinico needs complete control to ensure there
            # are no errors
            cron.remove_all('')

            # Setup the Pagespeed job
            if 'pagespeed_enabled' in request.POST:
                Data_Job.objects.filter(job_name='pagespeed').update(job_status=True,
                                                                     job_hour=pagespeed_hour,
                                                                     job_minute=pagespeed_minute)
                # Schedule the job
                job = cron.new(command='export PYTHONPATH=%s && %s/jobs/pagespeed.py' % (app_dir,app_dir),
                               comment='Quinico Pagespeed Data Job')
                nums = pagespeed_hour.split(',')
                for num in nums:
                    job.hour.on(num)
                job.minute.on(pagespeed_minute)
            else:
                Data_Job.objects.filter(job_name='pagespeed').update(job_status=False,
  								     job_hour=pagespeed_hour,
                                                                     job_minute=pagespeed_minute)

            # Setup the Webmaster job
            if 'webmaster_enabled' in request.POST:
                Data_Job.objects.filter(job_name='webmaster').update(job_status=True,
                                                                     job_hour=webmaster_hour,
                                                                     job_minute=webmaster_minute)
                # Schedule the job
                job = cron.new(command='export PYTHONPATH=%s && %s/jobs/webmaster.py' % (app_dir,app_dir),
                               comment='Quinico Webmaster Data Job')
                job.hour.on(webmaster_hour)
                job.minute.on(webmaster_minute)
            else:
                Data_Job.objects.filter(job_name='webmaster').update(job_status=False,
  								     job_hour=webmaster_hour,
                                                                     job_minute=webmaster_minute)

            # Setup the SEOMoz job
            if 'seomoz_enabled' in request.POST:
                Data_Job.objects.filter(job_name='seomoz').update(job_status=True,
                                                                     job_hour=seomoz_hour,
                                                                     job_minute=seomoz_minute)
                # Schedule the job
                job = cron.new(command='export PYTHONPATH=%s && %s/jobs/seomoz.py' % (app_dir,app_dir),
                               comment='Quinico SEOMoz Data Job')
                job.hour.on(seomoz_hour)
                job.minute.on(seomoz_minute)
            else:
                Data_Job.objects.filter(job_name='seomoz').update(job_status=False,
  								     job_hour=seomoz_hour,
                                                                     job_minute=seomoz_minute)

            # Setup the Keyword Rank job
            if 'keyword_rank_enabled' in request.POST:
                Data_Job.objects.filter(job_name='keyword_rank').update(job_status=True,
                                                                     job_hour=keyword_rank_hour,
                                                                     job_minute=keyword_rank_minute)
                # Schedule the job
                job = cron.new(command='export PYTHONPATH=%s && %s/jobs/keyword_rank.py' % (app_dir,app_dir),
                               comment='Quinico Keyword Rank Data Job')
                job.hour.on(keyword_rank_hour)
                job.minute.on(keyword_rank_minute)
            else:
                Data_Job.objects.filter(job_name='keyword_rank').update(job_status=False,
  								     job_hour=keyword_rank_hour,
                                                                     job_minute=keyword_rank_minute)

            # Setup the Webpagetest job
            if 'webpagetest_enabled' in request.POST:
                Data_Job.objects.filter(job_name='webpagetest').update(job_status=True,
                                                                     job_hour=webpagetest_hour,
                                                                     job_minute=webpagetest_minute)
                # Schedule the job
                job = cron.new(command='export PYTHONPATH=%s && %s/jobs/webpagetest.py' % (app_dir,app_dir),
                               comment='Quinico Webpagetest Data Job')
                nums = webpagetest_hour.split(',')
                for num in nums:
                    job.hour.on(num)
                job.minute.on(webpagetest_minute)
            else:
                Data_Job.objects.filter(job_name='webpagetest').update(job_status=False,
  								     job_hour=webpagetest_hour,
                                                                     job_minute=webpagetest_minute)

            # Write out the crontab
            cron.write()

            # Redirect back
            return HttpResponseRedirect('/admin/datajobs')
      
    # Not a POST so create a blank form
    else:
        form = JobsForm()

    # Obtain what Quinico says should be scheduled 
    jobs = Data_Job.objects.values('job_name','job_status','job_hour','job_minute')

    # Now obtain what the cron tab says is scheduled (if debug is requested)
    if 'debug' in request.GET:
        cron = CronTab()
    else:
        cron = None

    # Check if any jobs are running
    for job in jobs:
        file = '%s/jobs/pid/%s.pid' % (app_dir,job['job_name'])
        if os.path.exists(file):
            pidfile = open(file, "r")
            pidfile.seek(0)
            pid = pidfile.readline()

            # See if the PID is running
            if os.path.exists('/proc/%s' % pid):
                job['running'] = True
            else:
                job['running'] = False
        else:
            job['running'] = False

    # Print the page
    return render_to_response(
       'main/datajobs.html',
       {
          'title':'Quinico | Data Job Manager',
          'jobs':jobs,
          'cron':cron,
          'form':form
       },
       context_instance=RequestContext(request)
    )


@staff_member_required
def config(request):
    """Configuration Parameters

    """

    if request.method == 'POST':

        # Check the form elements
        # We'll only update values if the user indicates they want it by checking the box
        form = ConfigForm(request.POST)

        if form.is_valid():

            # Obtain the cleaned data and put into a lookup table
            params = {}
            params['google_key'] = form.cleaned_data['google_key']
            params['google_se_id'] = form.cleaned_data['google_se_id']
            params['google_wm_username'] = form.cleaned_data['google_wm_username']
            params['google_wm_password'] = form.cleaned_data['google_wm_password']
            params['max_google_api_calls'] = form.cleaned_data['max_google_api_calls']
            params['max_keyword_results'] = form.cleaned_data['max_keyword_results']
            params['seomoz_access_id'] = form.cleaned_data['seomoz_access_id']
            params['seomoz_account_type'] = form.cleaned_data['seomoz_account_type']
            params['seomoz_secret_key'] = form.cleaned_data['seomoz_secret_key']
            params['pagespeed_locale'] = form.cleaned_data['pagespeed_locale']
            params['pagespeed_threads'] = form.cleaned_data['pagespeed_threads']
            params['smtp_notify_data_start'] = form.cleaned_data['smtp_notify_data_start']
            params['smtp_notify_seomoz_new'] = form.cleaned_data['smtp_notify_seomoz_new']
            params['wpt_attempts'] = form.cleaned_data['wpt_attempts']
            params['wpt_key'] = form.cleaned_data['wpt_key']
            params['wpt_wait'] = form.cleaned_data['wpt_wait']
            params['wpt_threads'] = form.cleaned_data['wpt_threads']
            params['dashboard_refresh'] = form.cleaned_data['dashboard_refresh']
            params['dashboard_slots'] = form.cleaned_data['dashboard_slots']
            params['dashboard_width'] = form.cleaned_data['dashboard_width']
            params['dashboard_height'] = form.cleaned_data['dashboard_height']
            params['dashboard_font'] = form.cleaned_data['dashboard_font']
            params['dashboard_frequency'] = form.cleaned_data['dashboard_frequency']
            params['alert'] = form.cleaned_data['alert']
            params['disable_pagespeed_reports'] = form.cleaned_data['disable_pagespeed_reports']
            params['disable_keyword_rank_reports'] = form.cleaned_data['disable_keyword_rank_reports']
            params['disable_webmaster_reports'] = form.cleaned_data['disable_webmaster_reports']
            params['disable_seomoz_reports'] = form.cleaned_data['disable_seomoz_reports']
            params['disable_webpagetest_reports'] = form.cleaned_data['disable_webpagetest_reports']
            params['report_path'] = form.cleaned_data['report_path']

            # Update the data
            for param in params:
                if 'update_%s' % param in request.POST:
                    print '%s is being updated' % param
                    Config.objects.filter(config_name=param).update(config_value=params[param])

            # Redirect back
            return HttpResponseRedirect('/admin/config')

    # Not a POST so create a blank form and return all the existing configs
    else:
        form = ConfigForm()

    configs = Config.objects.values('config_name',
				    'friendly_name',
				    'config_value',
				    'description',
				    'display').order_by('friendly_name')

    # Print the page
    return render_to_response(
       'main/config.html',
       {
          'title':'Quinico | Configuration Manager',
          'form':form,
          'configs':configs
       },
       context_instance=RequestContext(request)
    )
