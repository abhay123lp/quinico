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


"""This module contains all of the views for the Quinico Webmaster
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
from django.db.models import Sum
from quinico.main.models import Config
from quinico.webmaster.models import Domain
from quinico.webmaster.models import Crawl_Error
from quinico.webmaster.models import Crawl_Error_Type
from quinico.webmaster.models import Top_Search_Queries
from quinico.webmaster.forms import QueriesForm
from quinico.webmaster.forms import CrawlErrorTrendForm
from quinico.webmaster.forms import TotalCrawlErrorTrendForm
from quinico.webmaster.forms import CrawlErrorSummaryForm
from quinico.dashboard.models import Dash_Settings


# Get an instance of a logger
logger = logging.getLogger(__name__)


def queries(request):
    """Google Search Queries Trends View
    Allow graphing of impressions and clicks in Google search for keywords
    that are being tracked for specific domains

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = QueriesForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            date_to = form.cleaned_data['date_to']
            date_from = form.cleaned_data['date_from']
            keyword = form.cleaned_data['keyword']
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

	    # Obtain the top search queries for this keyword and domain
	    data = Top_Search_Queries.objects.filter(domain__domain=domain,
                                                     keyword__keyword=keyword,
 						     date__range=[date_from,date_to]
     					            ).values('date','impressions','clicks').order_by('date')

	    # Construct the dashboard, download and monitoring links
            # Quote special characters
            keyword_enc = urllib.quote_plus(keyword.encode('utf-8'))
 
            base_url = 'http://%s/webmaster/queries?domain' % request.META['HTTP_HOST']
	    db_link = '%s=%s&keyword=%s&format=db' % (base_url,domain,keyword_enc)
	    json_link = '%s=%s&keyword=%s&format=json' % (base_url,domain,keyword_enc)
	    csv_link = '%s=%s&keyword=%s&date_from=%s&date_to=%s&format=csv' % (base_url,domain,keyword_enc,date_from,date_to)

	    # Print the page

	    # If this is a request for special formatting, give it, otherwise give everything
	    if format:
		# JSON request
		if format == 'json':
                    return HttpResponse(simplejson.dumps([{'date': row['date'].strftime("%Y-%m-%d"),
  							   'impressions': row['impressions'],
							   'clicks': row['clicks']} for row in data]),
                                        mimetype="application/json")
                    
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
		     'webmaster/queries-db.html',
		      {
			'title':'Quinico | Google Top Search Queries',
			'domain':domain,
			'keyword_name':keyword,
			'data':data,
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
		    writer.writerow(['date','impressions','clicks'])
		    for item in data:
			writer.writerow([item['date'],item['impressions'],item['clicks']])
		    return response

	    # Just a standard HTML response is being requested
	    else:
		return render_to_response(
		 'webmaster/queries.html',
		  {
		    'title':'Quinico | Google Top Search Queries',
		    'domain_name':domain,
		    'keyword_name':keyword,
		    'data':data,
		    'db_link':db_link,
		    'json_link':json_link,
		    'csv_link':csv_link
		  },
		  context_instance=RequestContext(request)
		)

    # Ok, its not a form submit
    else:
        form = QueriesForm()

    # Create a dictionary of all domains and keywords
    # to pass to the template so we can create the javascript to
    # dynamically populate the dropdowns
    kw_dict = {}

    # Obtain the domain list
    domain_list = Domain.objects.all()

    # Populate keywords for each domain
    for d in domain_list:
        # Obtain the keyword list
        keyword_list = Top_Search_Queries.objects.filter(domain__domain=d).values('keyword__keyword').distinct().order_by('keyword__keyword')
        # Add the list of keywords to the dictionary
        kw_dict[d] = keyword_list

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Print the page
    return render_to_response(
       'webmaster/queries_index.html',
       {
          'title':'Quinico | Google Top Search Queries',
          'form':form,
          'list':kw_dict,
          'date_to':date_to,
          'date_from':date_from
       },
       context_instance=RequestContext(request)
    )


def trends(request):
    """Webmaster Crawl Error Trends View
    Allow graphing of individual crawl error counts over time

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = CrawlErrorTrendForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            error_id = form.cleaned_data['error_id']
            date_to = form.cleaned_data['date_to']
            date_from = form.cleaned_data['date_from']
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

	    # Obtain the error counts for this domain and error type
	    counts = Crawl_Error.objects.filter(domain__domain=domain,
						type_id=error_id,
						date__range=[date_from,date_to]
					       ).values('date','count').order_by('date')

	    # Obtain the friendly error name for the report
	    error_name = Crawl_Error_Type.objects.filter(id=error_id).values('type')

	    # Construct the dashboard, download and monitoring links
            base_url = 'http://%s/webmaster/trends?domain' % request.META['HTTP_HOST']
	    db_link = '%s=%s&error_id=%s&format=db' % (base_url,domain,error_id)
	    json_link = '%s=%s&error_id=%s&format=json' % (base_url,domain,error_id)
	    csv_link = '%s=%s&error_id=%s&date_from=%s&date_to=%s&format=csv' % (base_url,domain,error_id,date_from,date_to)

	    # Print the page

	    # If this is a request for special formatting, give it, otherwise give everything
	    if format:
		# Dashboard request
		if format == 'db':
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
		     'webmaster/trends-db.html',
		      {
			'title':'Quinico | Webmaster Crawl Error Trends',
			'domain':domain,
			'error_name':error_name,
			'counts':counts,
			'dash_settings':dash_settings
		      },
		      mimetype='application/json',
		      context_instance=RequestContext(request)
		    )

		# JSON request
		elif format == 'json':
                    return HttpResponse(simplejson.dumps([{'date': row['date'].strftime("%Y-%m-%d"),
							   'count': row['count']} for row in counts]),
                                        mimetype="application/json")

		# CSV download (there is no template for this)
		elif format == 'csv':
		    response = HttpResponse(mimetype='text/csv')
		    response['Content-Disposition'] = 'attachment;filename=quinico_data.csv'
		    writer = csv.writer(response)
		    writer.writerow(['date','count'])
		    for item in counts:
			writer.writerow([item['date'],item['count']])
		    return response

	    # Just a standard HTML response is being requested
	    else:
		return render_to_response(
		   'webmaster/trends.html',
		   {
		    'title':'Quinico | Webmaster Crawl Error Trends',
		    'domain':domain,
		    'error_name':error_name,
		    'counts':counts,
		    'db_link':db_link,
		    'json_link':json_link,
		    'csv_link':csv_link
		   },
		   context_instance=RequestContext(request)
		)

    # Ok, its not a form submit
    else:
        form = CrawlErrorTrendForm()

    # Obtain the domains list
    domains = Domain.objects.all().order_by('domain')

    # Obtain the crawl error types
    error_types = Crawl_Error_Type.objects.all()

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Print the page
    return render_to_response(
       'webmaster/trends_index.html',
       {
          'title':'Quinico | Webmaster Crawl Error Trends',
          'form':form,
          'domains':domains,
          'error_types':error_types,
          'date_from':date_from,
	  'date_to':date_to
       },
       context_instance=RequestContext(request)
    )


def total(request):
    """Webmaster Total Crawl Error Trends View
    Allow graphing of the total crawl error counts over time

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = TotalCrawlErrorTrendForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            date_to = form.cleaned_data['date_to']
            date_from = form.cleaned_data['date_from']
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

	    # Obtain the error counts for this domain and error type
	    counts = Crawl_Error.objects.filter(domain__domain=domain,
					        date__range=[date_from,date_to]
					       ).values('date').annotate(Sum('count')).order_by('date')

	    # Construct the dashboard, download and monitoring links
            base_url = 'http://%s/webmaster/total?domain' % request.META['HTTP_HOST']
	    db_link = '%s=%s&format=db' % (base_url,domain)
	    json_link = '%s=%s&format=json' % (base_url,domain)
	    csv_link = '%s=%s&date_from=%s&date_to=%s&format=csv' % (base_url,domain,date_from,date_to)

	    # Print the page

	    # If this is a request for special formatting, give it, otherwise give everything
	    if format:
		# Dashboard request
		if format == 'db':
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
		     'webmaster/total-db.html',
		      {
			'title':'Quinico | Total Webmaster Crawl Error Trends',
			'domain':domain,
			'counts':counts,
			'dash_settings':dash_settings
		      },
		      mimetype='application/json',
		      context_instance=RequestContext(request)
		    )

		# JSON request
		elif format == 'json':
                    return HttpResponse(simplejson.dumps([{'date': row['date'].strftime("%Y-%m-%d"),
							   'count': row['count__sum']} for row in counts]),
                                        mimetype="application/json")

		# CSV download (there is no template for this)
		elif format == 'csv':
		    response = HttpResponse(mimetype='text/csv')
		    response['Content-Disposition'] = 'attachment;filename=quinico_data.csv'
		    writer = csv.writer(response)
		    writer.writerow(['date','count'])
		    for item in counts:
			writer.writerow([item['date'],item['count']])
		    return response

	    # Just a standard HTML response is being requested
	    else:
		return render_to_response(
		   'webmaster/total.html',
		   {
		    'title':'Quinico | Total Webmaster Crawl Error Trends',
		    'domain':domain,
		    'counts':counts,
		    'db_link':db_link,
		    'json_link':json_link,
		    'csv_link':csv_link
		   },
		   context_instance=RequestContext(request)
		)

    # Ok, its not a form submit
    else:
        form = TotalCrawlErrorTrendForm()

    # Obtain the domains list
    domains = Domain.objects.all().order_by('domain')

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Print the page
    return render_to_response(
       'webmaster/total_index.html',
       {
          'title':'Quinico | Webmaster Total Crawl Error Trends',
          'domains':domains,
          'date_from':date_from,
          'date_to':date_to
       },
       context_instance=RequestContext(request)
    )


def summary(request):
    """Webmaster Crawl Error Summary View
    Display all crawl error categories/counts for a single day

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = CrawlErrorSummaryForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            date = form.cleaned_data['date']

            # If the date is missing, set it b/c this is probably
            # an API or DB request
            if not date:
                now = datetime.datetime.today()
                date_to = now.strftime("%Y-%m-%d")

            # Create forward/backward links for navigation
            ref = datetime.datetime.strptime(date,'%Y-%m-%d')
            date_back = (ref - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            back_link = '/webmaster/summary?domain=%s&date=%s' % (domain,date_back)
            date_forward = (ref + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            forward_link = '/webmaster/summary?domain=%s&date=%s' % (domain,date_forward)
            
	    # Obtain the errors and counts for this domain
	    errors = Crawl_Error.objects.filter(domain__domain=domain,
						date=date
					       ).values('type__type','count')

	    # If there is no data, let the user know
	    if not errors:
	       message = 'The report returned no data.  Domain:%s, Date:%s' % (domain,date)
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

	    # Print the page
	    return render_to_response(
	       'webmaster/summary.html',
	       {
		  'title':'Quinico | Webmaster Crawl Error Summary',
		  'date':date,
		  'domain':domain,
                  'back_link':back_link,
                  'forward_link':forward_link,
		  'errors':errors
	       },
	       context_instance=RequestContext(request)
	    )

    # Ok, its not a form submit
    else:
        form = CrawlErrorSummaryForm()

    # Obtain the domains list
    domains = Domain.objects.all().order_by('domain')

    # Obtain the current date
    date = datetime.datetime.today()

    # Print the page
    return render_to_response(
       'webmaster/summary_index.html',
       {
          'title':'Quinico | Webmaster Crawl Error Summary',
          'form':form,
          'domains':domains,
          'date':date
       },
       context_instance=RequestContext(request)
    )

