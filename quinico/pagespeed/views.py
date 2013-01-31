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


"""This module contains all of the views for the Quinico Pagespeed
   application

"""


import datetime
import logging
import urllib
import csv
from django.utils import simplejson
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from quinico.main.models import Config
from quinico.pagespeed.models import Domain
from quinico.pagespeed.models import Url
from quinico.pagespeed.models import Score
from quinico.pagespeed.models import Test
from quinico.pagespeed.forms import PagespeedTrendForm
from quinico.pagespeed.forms import PagespeedBreakdownForm
from quinico.pagespeed.forms import PagespeedHistoryForm
from quinico.dashboard.models import Dash_Settings


# Get an instance of a logger
logger = logging.getLogger(__name__)


def trends(request):
    """Pagespeed Trends View
    Allow graphing of individual pagespeed metrics over time

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = PagespeedTrendForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            date_to = form.cleaned_data['date_to']
            date_from = form.cleaned_data['date_from']
            metric = form.cleaned_data['metric']
            url = form.cleaned_data['url']
            strategy = form.cleaned_data['strategy']
            format = form.cleaned_data['format']

            # If the from or to dates are missing, set them b/c this is probably
            # an API or DB request (just give the last 30 days of data)
            if not date_to or not date_from:
                now = datetime.datetime.today()
                date_to = now.strftime("%Y-%m-%d")

                # Move back 30 days
                then = datetime.timedelta(days=30)
                date_from = now - then
                date_from = date_from.strftime("%Y-%m-%d")

	    # Unquote the url to UTF-8 and then decode
	    u_unenc = urllib.unquote(url.encode('utf-8')).decode('utf-8')

	    # Obtain the scores for this test
	    scores = Score.objects.filter(test_id__domain__domain=domain,
                                          test_id__url__url=u_unenc,
                                          date__range=[date_from,date_to],
                                          strategy=strategy
                                         ).values('date',metric).order_by('date')

	    # Construct the dashboard, download and monitoring links
            base_url = 'http://%s/pagespeed/trends?domain=%s' % (request.META['HTTP_HOST'],domain)
	    db_link = '%s&url=%s&metric=%s&strategy=%s&format=db' % (base_url,url,metric,strategy)
	    json_link = '%s&url=%s&metric=%s&strategy=%s&format=json' % (base_url,url,metric,strategy)
	    csv_link = '%s&url=%s&metric=%s&strategy=%s&date_from=%s&date_to=%s&format=csv' % (base_url,
                                                                                               url,
                                                                                               metric,
                                                                                               strategy,
                                                                                               date_from,
                                                                                               date_to)

	    # Print the page

	    # If this is a request for special formatting, give it, otherwise give everything
	    if format:
                
		# JSON request
                if format == 'json':
                    return HttpResponse(simplejson.dumps([{'date': row['date'].strftime("%Y-%m-%d"),
                                                           metric: row[metric]} for row in scores]),
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
		     'pagespeed/trends-db.html',
		      {
			'title':'Quinico | Pagespeed Trends',
			'domain':domain,
			'strategy':strategy,
			'url':u_unenc,
			'metric':metric,
			'scores':scores,
			'dash_settings':dash_settings
		      },
		      mimetype='application/json',
		      context_instance=RequestContext(request)
		    )

		# CSV download (there is no template for this)
		elif format == 'csv':
		    response = HttpResponse(mimetype='text/csv')
		    response['Content-Disposition'] = 'attachment;filename=quinico_data.csv'
		    writer = csv.writer(response)
		    writer.writerow(['date','value'])
		    for row in scores:
			writer.writerow([row['date'],row[metric]])
		    return response

	    # Just a standard HTML response is being requested
	    else:
		return render_to_response(
		   'pagespeed/trends.html',
		   {
		      'title':'Quinico | Pagespeed Trends',
		      'domain':domain,
		      'strategy':strategy,
		      'url':u_unenc,
		      'metric':metric,
		      'scores':scores,
		      'db_link':db_link,
		      'json_link':json_link,
		      'csv_link':csv_link

		   },
		   context_instance=RequestContext(request)
		)

    # Ok, its not a form submit
    else:
        form = PagespeedTrendForm()

    # Obtain the domain list
    domains = Domain.objects.all().order_by('domain')

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Create a dictionary of all domains and urls
    # to pass to the template so we can create the javascript to
    # dynamically populate the dropdowns
    url_dict = {}

    # Populate urls for each domain
    for d in domains:
        # Obtain the url list
        urls = Test.objects.filter(domain__domain=d).values('url__url')

        # Add the list of urls to the dictionary
        url_dict[d] = urls

    # Print the page
    return render_to_response(
       'pagespeed/trends_index.html',               
       {
          'title':'Quinico | Pagespeed Trends',
          'form':form,
          'domains':domains,
          'url_dict':url_dict,
          'date_from':date_from,
          'date_to':date_to
       },
       context_instance=RequestContext(request)
    )


def breakdown(request):
    """Pagespeed Page Breakdown View
    Allow visual representation of page components

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = PagespeedBreakdownForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            date = form.cleaned_data['date']
            url = form.cleaned_data['url']
            strategy = form.cleaned_data['strategy']
            format = form.cleaned_data['format']

	    # Unquote the url to UTF-8 and then decode
	    u_unenc = urllib.unquote(url.encode('utf-8')).decode('utf-8')

	    # If the date is missing, set it b/c this is probably
	    # an API or DB request (just give the most recent)
            if not date:
		logger.debug('Obtaining last run of pagespeed for %s with %s' % (domain,strategy))
		last_run = Score.objects.filter(test_id__domain__domain=domain,
                                                test_id__url__url=u_unenc,
                                                strategy=strategy
                                               ).values('date').order_by('-date')[:1]
	   
		if last_run[0]['date']:
		    date = last_run[0]['date']
		    logger.debug('Last run of pagespeed: %s' % date)
		else:
		    logger.debug('pagespeed data collection has never been run')

            # Create forward/backward links for navigation if this is not an API request
            if not format:
                ref = datetime.datetime.strptime(date,'%Y-%m-%d')
                date_back = (ref - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                back_link = '/pagespeed/breakdown?domain=%s&url=%s&strategy=%s&date=%s' % (domain,url,strategy,date_back)
                date_forward = (ref + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                forward_link = '/pagespeed/breakdown?domain=%s&url=%s&strategy=%s&date=%s' % (domain,url,strategy,date_forward)

	    # Obtain the data for this domain for the date in question
	    scores = Score.objects.filter(test_id__domain__domain=domain,
                                          test_id__url__url=u_unenc,
                                          date=date,strategy=strategy
                                         ).values('test_id__url__url',
					          'numberResources',
					          'numberStaticResources',
					          'numberCssResources',
					          'totalRequestBytes',
					          'textResponseBytes',
					          'cssResponseBytes',
					          'htmlResponseBytes',
					          'imageResponseBytes',
					          'javascriptResponseBytes',
					          'otherResponseBytes',
					         )

            # If there is no data, let the user know
            if not scores:
               message = 'The report returned no data.  Domain:%s, Url:%s, Strategy:%s, Date:%s' % (domain,url,strategy,date)
               return render_to_response(
                   'misc/generic.html',
                   {
                    'title':'Quinico | No Data',
                    'back_link':back_link,
                    'forward_link':forward_link,
                    'message':message
                   },
                   context_instance=RequestContext(request)
                )

	    # Construct an alternate strategy URL
	    if strategy == 'desktop':
		a_strategy = 'mobile'
	    elif strategy == 'mobile':
		a_strategy = 'desktop'
	    else:
		a_strategy = strategy
            base_url = 'http://%s/pagespeed/breakdown?domain' % (request.META['HTTP_HOST'])
	    a_url = '%s=%s&url=%s&date=%s&strategy=%s' % (base_url,domain,url,date,a_strategy)

	    # Construct the dashboard, download and monitoring links
	    db_link = '%s=%s&url=%s&strategy=%s&format=db' % (base_url,domain,url,strategy)
	    json_link = '%s=%s&url=%s&strategy=%s&format=json' % (base_url,domain,url,strategy)

	    # Print the page

	    # If this is a request for special formatting, give it, otherwise give everything
	    if format:
		# JSON request
		if format == 'json':
                    return HttpResponse(simplejson.dumps([row for row in scores]),
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
		     'pagespeed/breakdown-db.html',
		      {
			'title':'Quinico | Pagespeed Breakdown',
			'date':date,
			'domain':domain,
			'url':u_unenc,
			'strategy':strategy,
			'scores':scores,
			'dash_settings':dash_settings
		      },
		      mimetype='application/json',
		      context_instance=RequestContext(request)
		    )

	    # Just a standard HTML response is being requested
	    else:
		return render_to_response(
		   'pagespeed/breakdown.html',
		   {
		      'title':'Quinico | Pagespeed Breakdown',
                      'back_link':back_link,
                      'forward_link':forward_link,
		      'date':date,
		      'domain':domain,
		      'url':u_unenc,
		      'strategy':strategy,
		      'scores':scores,
		      'a_url':a_url,
		      'db_link':db_link,
		      'json_link':json_link,
		   },
		   context_instance=RequestContext(request)
		)

    # Ok, its not a form submit
    else:
        form = PagespeedBreakdownForm()

    # Obtain the domain list
    domains = Domain.objects.all().order_by('domain')

    # Obtain the current date for the date field selector
    now = datetime.datetime.today()
    date = now.strftime("%Y-%m-%d")

    # Create a dictionary of all domains and urls
    # to pass to the template so we can create the javascript to
    # dynamically populate the dropdowns
    url_dict = {}

    # Populate urls for each domain
    for d in domains:
        # Obtain the url list
        urls = Test.objects.filter(domain__domain=d).values('url__url')

        # Add the list of urls to the dictionary
        url_dict[d] = urls

    # Print the page
    return render_to_response(
       'pagespeed/breakdown_index.html',
       {
          'title':'Quinico | Pagespeed Breakdown',
          'form':form,
          'domains':domains,
          'url_dict':url_dict,
          'date':date
       },
       context_instance=RequestContext(request)
    )


def history(request):
    """Pagespeed History View
    Allow presentation of raw pagespeed data for a defined time range

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = PagespeedHistoryForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            date_to = form.cleaned_data['date_to']
            date_from = form.cleaned_data['date_from']
            url = form.cleaned_data['url']
            strategy = form.cleaned_data['strategy']
            format = form.cleaned_data['format']

            # If the from or to dates are missing, set them b/c this is probably
            # an API or DB request (just give the last 30 days of data)
            if not date_to or not date_from:
                now = datetime.datetime.today()
                date_to = now.strftime("%Y-%m-%d")

                # Move back 30 days
                then = datetime.timedelta(days=30)
                date_from = now - then
                date_from = date_from.strftime("%Y-%m-%d")

	    # Unquote the url to UTF-8 and then decode
	    u_unenc = urllib.unquote(url.encode('utf-8')).decode('utf-8')

	    # Values that we'll export in CSV
	    headings = ['date','score','numberHosts','numberResources','numberStaticResources','numberCssResources',
			'totalRequestBytes','textResponseBytes','cssResponseBytes','htmlResponseBytes','imageResponseBytes',
			'javascriptResponseBytes','otherResponseBytes']

	    # Obtain the data
	    dates = Score.objects.filter(test_id__domain__domain=domain,
                                         test_id__url__url=u_unenc,
                                         date__range=[date_from,date_to],
                                         strategy=strategy
                                        ).values().order_by('-date')

	    # Construct the csv link
            base_url = 'http://%s/pagespeed/history?domain=%s' % (request.META['HTTP_HOST'],domain)
	    csv_link = '%s&url=%s&strategy=%s&date_from=%s&date_to=%s&format=csv' % (base_url,url,strategy,date_from,date_to)

	    # Print the page

	    # If this is a request for special formatting, give it, otherwise give everything
	    # Dashboard request
	    if format:
		# CSV download (there is no template for this)
		if request.GET['format'] == 'csv':
		    response = HttpResponse(mimetype='text/csv')
		    response['Content-Disposition'] = 'attachment;filename=quinico_data.csv'
		    writer = csv.writer(response)
		    writer.writerow(headings)
		    for row in dates:
			# Construct the next row
			wr = []
			for heading in headings:
			    wr.append(row[heading])
			# Add the row    
			writer.writerow(wr)
		    return response

	    # Just a standard HTML response is being requested
	    else:
		return render_to_response(
		   'pagespeed/history.html',
		   {
		      'title':'Quinico | Pagespeed History',
		      'domain':domain,
		      'strategy':strategy,
		      'url':u_unenc,
		      'dates':dates,
		      'csv_link':csv_link
		   },
		   context_instance=RequestContext(request)
		)

    # Ok, its not a form submit
    else:
        form = PagespeedHistoryForm()

    # Obtain the domain list
    domains = Domain.objects.all().order_by('domain')

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Create a dictionary of all domains and urls
    # to pass to the template so we can create the javascript to
    # dynamically populate the dropdowns
    url_dict = {}

    # Populate keywords for each domain
    for d in domains:
        # Obtain the url list
        urls = Test.objects.filter(domain__domain=d).values('url__url')

        # Add the list of keywords to the dictionary
        url_dict[d] = urls

    # Print the page
    return render_to_response(
       'pagespeed/history_index.html',
       {
          'title':'Quinico | Pagespeed History',
          'domains':domains,
          'url_dict':url_dict,
          'date_from':date_from,
          'date_to':date_to

       },
       context_instance=RequestContext(request)
    )

