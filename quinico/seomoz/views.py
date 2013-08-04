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


"""This module contains all of the views for the Quinico SEOMoz
   application

"""

import urllib
import datetime
import logging
import csv
from django.utils import simplejson
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from quinico.seomoz.models import Url
from quinico.seomoz.models import Metrics
from quinico.seomoz.models import Competitor
from quinico.seomoz.models import Description
from quinico.main.models import Config
from quinico.dashboard.models import Dash_Settings
from quinico.seomoz.forms import SEOTrendForm
from quinico.seomoz.forms import SEODashboardForm


# Get an instance of a logger
logger = logging.getLogger(__name__)


def trends(request):
    """SEO Metrics Trends View
    Allow graphing of individual SEO metrics

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:

        # Check the form elements
        form = SEOTrendForm(request.GET)

        if form.is_valid():

            # Obtain the cleaned data
            url = form.cleaned_data['url']
            metric = form.cleaned_data['metric']
            date_to = form.cleaned_data['date_to']
            date_from = form.cleaned_data['date_from']
            format = form.cleaned_data['format']
            width = form.cleaned_data['width']
            height = form.cleaned_data['height']
            step = form.cleaned_data['step']

            # If the from or to dates are missing, set them b/c this is probably
            # an API or DB request (just give the last 30 days of data)
            if not date_to or not date_from:
                # One or both were not provided, so set them
                now = datetime.datetime.today()
                date_to = now.strftime("%Y-%m-%d")

                # Move back 180 days which should give us 6-10 data points
                then = datetime.timedelta(days=180)
                date_from = now - then
                date_from = date_from.strftime("%Y-%m-%d")

            # Obtain metrics for this url
            trends = Metrics.objects.filter(url__url=url,
                                            date__range=[date_from,date_to]).values('date',metric).order_by('date')

            # Obtain the human friendly name of the metric and if it should be represented in
            # the Google chart with decimals
            metric_details = Description.objects.filter(metric=metric).values('column_description','represent')

            # Construct the dashboard, download and monitoring links
            base_url = 'http://%s/seomoz/trends?url' % (request.META['HTTP_HOST'])
            db_link = '%s=%s&metric=%s&format=db' % (base_url,url,metric)
            json_link = '%s=%s&metric=%s&format=json' % (base_url,url,metric)
            csv_link = '%s=%s&metric=%s&date_from=%s&date_to=%s&format=csv' % (base_url,url,metric,date_from,date_to)

            # Print the page

            # If this is a request for special formatting, give it, otherwise give everything
            if format:
                # JSON request
                if format == 'json':
                    return HttpResponse(simplejson.dumps([{'date': row['date'].strftime("%Y-%m-%d"),
                                                           metric: str(row[metric])} for row in trends]),
                                        mimetype="application/json")

                # Dashboard request
                elif format == 'db':
                    # If the user is authenticated and has a preference for size, set it
                    dash_settings = None
                    if request.user.is_authenticated():
                        # Obtain the user's dashboard settings
                        dash_settings = Dash_Settings.objects.filter(user__username=request.user.username)

                    if not dash_settings:
                        # Give the default
                        dash_settings = [{'width':Config.objects.filter(config_name='dashboard_width').values('config_value')[0]['config_value'],
                                         'height':Config.objects.filter(config_name='dashboard_height').values('config_value')[0]['config_value'],
                                         'font':Config.objects.filter(config_name='dashboard_font').values('config_value')[0]['config_value']}]

                    return render_to_response(
                     'seomoz/trends-db.html',
                      {
                        'title':'Quinico | SEO Trends',
                        'url':url,
                        'metric_name':metric_details[0]['column_description'],
                        'trends':trends,
                        'dash_settings':dash_settings,
                        'width':width,
                        'height':height,
                        'step':step
                      },
                      context_instance=RequestContext(request)
                    )

                # CSV download (there is no template for this)
                elif format == 'csv':
                    response = HttpResponse(mimetype='text/csv')
                    response['Content-Disposition'] = 'attachment;filename=quinico_data.csv'
                    writer = csv.writer(response)
                    writer.writerow(['date','value'])
                    for row in trends:
                        writer.writerow([row['date'],row[metric]])
                    return response

            # Just a standard HTML response is being requested
            else:
                return render_to_response(
                 'seomoz/trends.html',
                  {
                    'title':'Quinico | SEO Trends',
                    'url':url,
                    'metric_name':metric_details[0]['column_description'],
                    'metric_represent':metric_details[0]['represent'],
                    'trends':trends,
                    'db_link':db_link,
                    'json_link':json_link,
                    'csv_link':csv_link
                  },
                  context_instance=RequestContext(request)
                )
        
        else:
            # Invalid form submit
            logger.error('Invalid form: SEOTrendForm: %s' % form.errors)

    # Ok, its not a form submit
    else:
        form = SEOTrendForm()

    # Obtain the url list
    urls = Url.objects.all().order_by('url')

    # See if the user has a free or paid account
    account_type = Config.objects.filter(config_name='seomoz_account_type').values('config_value')

    # Get the descriptions
    descriptions = Description.objects.values('metric','column_description','full_description')

    # Obtain the current date
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 180 days
    then = datetime.timedelta(days=180)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Print the page
    return render_to_response(
       'seomoz/trends_index.html',
       {
          'title':'Quinico | SEO Trends',
          'account_type':account_type,
          'descriptions':descriptions,
          'form':form,
          'urls':urls,
          'date_to':date_to,
          'date_from':date_from
       },
       context_instance=RequestContext(request)
    )


def dashboard(request):
    """SEO Metrics Dashboard Index Page
    Create a dashboard of SEO metrics (including competitors)

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = SEODashboardForm(request.GET)

        if form.is_valid():

            # Obtain the cleaned data
            url = form.cleaned_data['url']
            date = form.cleaned_data['date']
            format = form.cleaned_data['format']
           
            # If the date is not set, this is probably an API or DB request so set it
            if not date:
                last_date = Metrics.objects.values('date').distinct().order_by('-date')[:1]
                if last_date[0]:
                    date = last_date[0]['date']

            # See if the user has a free or paid account
            account_type = Config.objects.filter(config_name='seomoz_account_type').values('config_value')

            # Obtain the SEO metrics for this url and any competitors for the requested date
            metrics = Metrics.objects.filter(url__url=url,date=date).values('url','ueid','feid','peid','ujid','uifq','uipl','uid','fid','pid','umrp','fmrp','pmrp','utrp','ftrp','ptrp','uemrp','fejp','pejp','fjp','pjp','fuid','puid','fipl','upa','pda')

            # Check for competitors
            competitors = []
            comp_ids = Competitor.objects.filter(url__url=url).values('comp_id')
            if comp_ids:
                for id in comp_ids:
                    comp_data = Metrics.objects.filter(url_id=id['comp_id'],date=date).values('url__url','ueid','feid','peid','ujid','uifq','uipl','uid','fid','pid','umrp','fmrp','pmrp','utrp','ftrp','ptrp','uemrp','fejp','pejp','fjp','pjp','fuid','puid','fipl','upa','pda')
                    # If this competitor was added after the main url, there might not be data for it
                    if comp_data:
                        competitors.append(comp_data)


            # Construct the dashboard, download and monitoring links
            base_url = 'http://%s/seomoz/dashboard?url' % (request.META['HTTP_HOST'])
            csv_link = '%s=%s&date=%s&format=csv' % (base_url,url,date)

            # Print the page

            # If this is a request for special formatting, give it, otherwise give everything
            if format:
                # CSV download (there is no template for this)
                if format == 'csv':
                    response = HttpResponse(mimetype='text/csv')
                    response['Content-Disposition'] = 'attachment;filename=quinico_data.csv'
                    writer = csv.writer(response)
                    writer.writerow(['metric','value'])
                    writer.writerow(['date',date])
                    for key in metrics[0]:
                        writer.writerow([key,metrics[0][key]])
                    return response

            # Just a standard HTML response is being requested
            else:
                # Get the descriptions
                descriptions = Description.objects.values('metric','column_description','full_description')

                return render_to_response(
                 'seomoz/dashboard.html',
                  {
                    'title':'Quinico | SEO Dashboard',
                    'date':date,
                    'account_type':account_type,
                    'url':url,
                    'metrics':metrics,
                    'descriptions':descriptions,
                    'competitors':competitors,
                    'csv_link':csv_link
                  },
                  context_instance=RequestContext(request)
                )

    # Ok, its not a form submit
    else:
        form = SEODashboardForm()

    # Obtain the url list
    list = Url.objects.all().order_by('url')

    # Obtain the most recent 5 data collection dates
    # and the first date
    dates = Metrics.objects.values('date').distinct().order_by('-date')[:5]

    if dates:
        today = dates[0]
    else:
        return render_to_response(
         'error/nodata.html',
          {
            'title':'Quinico | No Data',
            'type':'seomoz'
          },
          context_instance=RequestContext(request)
        )

    # Print the page
    return render_to_response(
       'seomoz/dashboard_index.html',
       {
          'title':'Quinico | SEO Dashboard',
          'form':form,
          'list':list,
          'today':today,
          'dates':dates
       },
       context_instance=RequestContext(request)
    )



