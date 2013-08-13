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
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Sum, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from quinico.main.models import Config
from quinico.webmaster.models import Domain
from quinico.webmaster.models import Crawl_Error
from quinico.webmaster.models import Crawl_Error_Type
from quinico.webmaster.models import Top_Search_Queries
from quinico.webmaster.models import Messages
from quinico.webmaster.models import Message_Status
from quinico.webmaster.models import Message_Update
from quinico.webmaster.forms import QueriesForm
from quinico.webmaster.forms import CrawlErrorTrendForm
from quinico.webmaster.forms import TotalCrawlErrorTrendForm
from quinico.webmaster.forms import AllCrawlErrorTrendForm
from quinico.webmaster.forms import CrawlErrorSummaryForm
from quinico.webmaster.forms import MessageUpdateForm
from quinico.webmaster.forms import MessageDetailForm
from quinico.webmaster.forms import MessageForm
from quinico.webmaster.forms import MessageDeleteForm
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
			width = form.cleaned_data['width']
			height = form.cleaned_data['height']
			step = form.cleaned_data['step']

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
				     'webmaster/queries-db.html',
				      {
						'title':'Google Top Search Queries',
						'domain':domain,
						'keyword_name':keyword,
						'data':data,
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
				    writer.writerow(['date','impressions','clicks'])
				    for item in data:
						writer.writerow([item['date'],item['impressions'],item['clicks']])
				    return response

			# Just a standard HTML response is being requested
			else:
				return render_to_response(
				 'webmaster/queries.html',
				  {
				    'title':'Google Top Search Queries',
				    'domain_name':domain,
				    'keyword_name':keyword,
				    'data':data,
				    'db_link':db_link,
				    'json_link':json_link,
				    'csv_link':csv_link
				  },
				  context_instance=RequestContext(request)
				)

        else:
            # Invalid form submit
            logger.error('Invalid form: QueriesForm: %s' % form.errors)

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
          'title':'Google Top Search Queries',
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
			width = form.cleaned_data['width']
			height = form.cleaned_data['height']
			step = form.cleaned_data['step']

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
						'title':'Webmaster Crawl Error - Individual Trends',
						'domain':domain,
						'error_name':error_name,
						'counts':counts,
						'dash_settings':dash_settings,
			            'width':width,
			            'height':height,
			            'step':step
				      },
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
				    'title':'Webmaster Crawl Error - Individual Trends',
				    'domain':domain,
				    'error_name':error_name,
				    'counts':counts,
				    'db_link':db_link,
				    'json_link':json_link,
				    'csv_link':csv_link
				   },
				   context_instance=RequestContext(request)
				)

        else:
            # Invalid form submit
            logger.error('Invalid form: CrawlErrorTrendForm: %s' % form.errors)

    # Its not a form submit, or its a failed form submit
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
          'title':'Webmaster Crawl Error - Individual Trends',
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
			width = form.cleaned_data['width']
			height = form.cleaned_data['height']
			step = form.cleaned_data['step']

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
			counts = Crawl_Error.objects.filter(domain__domain=domain,date__range=[date_from,date_to]
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
						'title':'Webmaster Crawl Error - Domain Total',
						'domain':domain,
						'counts':counts,
						'dash_settings':dash_settings,
			            'width':width,
			            'height':height,
			            'step':step
				      },
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
				    'title':'Webmaster Crawl Error - Domain Total',
				    'domain':domain,
				    'counts':counts,
				    'db_link':db_link,
				    'json_link':json_link,
				    'csv_link':csv_link
				   },
				   context_instance=RequestContext(request)
				)

        else:
            # Invalid form submit
            logger.error('Invalid form: TotalCrawlErrorTrendForm: %s' % form.errors)

    # Its not a form submit, or its a failed form submit
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
          'title':'Webmaster Crawl Error - Domain Total',
          'domains':domains,
          'date_from':date_from,
          'date_to':date_to
       },
       context_instance=RequestContext(request)
    )


def all(request):
    """Webmaster All Crawl Error Trends View (so, everything)

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = AllCrawlErrorTrendForm(request.GET)

        if form.is_valid():
			# Obtain the cleaned data
			date_to = form.cleaned_data['date_to']
			date_from = form.cleaned_data['date_from']
			format = form.cleaned_data['format']
			width = form.cleaned_data['width']
			height = form.cleaned_data['height']
			step = form.cleaned_data['step']

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
			counts = Crawl_Error.objects.filter(date__range=[date_from,date_to]
						       				   ).values('date').annotate(Sum('count')).order_by('date')

			# Construct the dashboard, download and monitoring links
			base_url = 'http://%s/webmaster/all?' % request.META['HTTP_HOST']
			db_link = '%sformat=db' % (base_url)
			json_link = '%sformat=json' % (base_url)
			csv_link = '%sdate_from=%s&date_to=%s&format=csv' % (base_url,date_from,date_to)

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
				     'webmaster/all-db.html',
				      {
						'title':'Webmaster Crawl Error Trends - All',
						'counts':counts,
						'dash_settings':dash_settings,
			            'width':width,
			            'height':height,
			            'step':step
				      },
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
				   'webmaster/all.html',
				   {
				    'title':'Webmaster Crawl Error Trends - All',
				    'counts':counts,
				    'db_link':db_link,
				    'json_link':json_link,
				    'csv_link':csv_link
				   },
				   context_instance=RequestContext(request)
				)

        else:
            # Invalid form submit
            logger.error('Invalid form: AllCrawlErrorTrendForm: %s' % form.errors)

    # Its not a form submit, or its a failed form submit
    else:
        form = AllCrawlErrorTrendForm()

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Print the page
    return render_to_response(
       'webmaster/all_index.html',
       {
          'title':'Webmaster Crawl Error Trends - All',
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

			# Create forward/backward links for navigation
			date_back = (date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
			back_link = '/webmaster/summary?domain=%s&date=%s' % (domain,date_back)
			date_forward = (date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
			forward_link = '/webmaster/summary?domain=%s&date=%s' % (domain,date_forward)
            
		# Obtain the errors and counts for this domain
		errors = Crawl_Error.objects.filter(domain__domain=domain,date=date).values('type__type','count')

		# If there is no data, let the user know
		if not errors:
			message = 'The report returned no data.  Domain:%s, Date:%s' % (domain,date)
			return render_to_response(
			   'misc/generic.html',
			   {
			    'title':'No Data',
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
		  'title':'Webmaster Crawl Error - Daily Summary',
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
          'title':'Webmaster Crawl Error - Daily Summary',
          'form':form,
          'domains':domains,
          'date':date
       },
       context_instance=RequestContext(request)
    )


def messages(request):
	"""Webmaster Messages
	Display and manage Google webmaster messages

	"""

	form = MessageForm(request.GET)

	# Check the params
	if form.is_valid():

		page = form.cleaned_data['page']
		filter = form.cleaned_data['filter']
		format = form.cleaned_data['format']
		color = form.cleaned_data['color']
		size = form.cleaned_data['size']

		# Construct the dashboard link
		db_link = 'http://%s/webmaster/messages?format=db' % request.META['HTTP_HOST']

		# If this is a dashboard request, get the desired messages and return, otherwise, process with the paginator/filter
		# If this is a request for special formatting, give it, otherwise give everything
		if format:
			# Dashboard request
			if format == 'db':
				# Give the newest 2 messages
				messages = Messages.objects.values('date_discovered','subject').order_by('-date_discovered')[:5]

			    # Print the page
				return render_to_response(
			       'webmaster/messages-db.html',
			       {
			          'title':'Webmaster Messages',
			          'messages':messages,
			          'color':color,
	          		  'size':size
			       },
			       context_instance=RequestContext(request)
			    )

		# Obtain the possible statuses for filtering
		statuses = Message_Status.objects.values('id','status').order_by('status')

		# We'll show these in pages but first select them all
		# If there is no filter or filter is empty, select everything, otherwise filter
		if filter:
			message_list = Messages.objects.filter(status_id=filter).values('id','date','date_discovered','subject','status__status').annotate(num_updates=Count('message_update')).order_by('-date_discovered')
		else:
			message_list = Messages.objects.values('id','date','date_discovered','subject','status__status').annotate(num_updates=Count('message_update')).order_by('-date_discovered')

		paginator = Paginator(message_list, 20) # Show 20 messages per page
		    
		try:
			msgs = paginator.page(page)
		except PageNotAnInteger:
			# If page is not an integer, or is not given deliver first page.
			msgs = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			msgs = paginator.page(paginator.num_pages)
    
	    # Print the page
		return render_to_response(
	       'webmaster/messages.html',
	       {
	          'title':'Webmaster Messages',
	          'statuses':statuses,
	          'msgs':msgs,
	          'filter':filter,
	          'db_link':db_link
	       },
	       context_instance=RequestContext(request)
	    )

	# Invalid form
	else:
		logger.error('Invalid Form: %s.  Error: %s' % ('MessageForm',form.errors))
		return HttpResponseRedirect('/webmaster/messages')


@login_required
@staff_member_required
def message_update(request):
	"""Webmaster Messages Detail
	Update Google Webmaster Message Detail
	
	"""

	# We only accept POSTs to this view
	if request.method == 'POST':
		# Check the form elements
		form = MessageUpdateForm(request.POST)

		if form.is_valid():
			# Obtain the cleaned data
			id = form.cleaned_data['id']
			update = form.cleaned_data['update']
			status = form.cleaned_data['status']

			# Get the user's ID
			user_id = User.objects.filter(username=request.user.username).values('id')[0]['id']
			
			# Add the update
			Message_Update(message_id=id,user_id=user_id,update=update).save()
			
			# Update the message status
			Messages.objects.filter(id=id).update(status=status)

			# Send them to the message detail page with the updated data
			return HttpResponseRedirect('/webmaster/message_detail?id=%s' % id)

		# Invalid form submit, give them the detail view again, but with form errors
		else:
			logger.error('Invalid Form: %s.  Error: %s' % ('MessageUpdateForm',form.errors))

			# Obtain detail about this message (we'll need the message ID)
			if not 'id' in request.POST:
				# Need to redirect then
				return HttpResponseRedirect('/webmaster/messages')
			else:
				id = request.POST['id']

			detail = Messages.objects.filter(id=id).values('body','status__status')
			statuses = Message_Status.objects.values('id','status').order_by('status')
			updates = Message_Update.objects.filter(message_id=id).values('date','user_id__first_name','user_id__last_name','update')

			# Print the page
			return render_to_response(
		       'webmaster/message_detail.html',
		       {
		          'title':'Webmaster Message Detail',
		          'form':form,
		          'id':id,
		          'detail':detail,
		          'statuses':statuses,
		          'updates':updates
		       },
		       context_instance=RequestContext(request)
		    )			
	
	# Not a POST so redirect back to messages
	else:
		logger.error('Received a GET to /webmaster/message_update')
		return HttpResponseRedirect('/webmaster/messages')

	
def message_detail(request):
	"""Webmaster Messages Detail
	Display Google Webmaster Message Detail
	
	"""

	form = MessageDetailForm(request.GET)
    
	# Check the params
	if form.is_valid():
		# Obtain the cleaned data
		id = form.cleaned_data['id']
    
	# Invalid params
	else:
		logger.error('Invalid Form: %s' % 'MessageDetailForm')
		return HttpResponseRedirect('/webmaster/messages')
    	
	detail = Messages.objects.filter(id=id).values('subject','body','status__status')
	statuses = Message_Status.objects.values('id','status').order_by('status')
	updates = Message_Update.objects.filter(message_id=id).values('date','user_id__first_name','user_id__last_name','update')

	# Print the page
	return render_to_response(
       'webmaster/message_detail.html',
       {
          'title':'Webmaster Message Detail',
          'id':id,
          'detail':detail,
          'statuses':statuses,
          'updates':updates
       },
       context_instance=RequestContext(request)
    )

@login_required
@staff_member_required
def message_delete(request):
	"""Delete Webmaster Messages
	
	"""

	form = MessageDeleteForm(request.GET)
    
	# Check the params
	if form.is_valid():
		# Obtain the cleaned data
		id = form.cleaned_data['id']

		# Delete the message	
		Messages.objects.filter(id=id).delete()

		# Redirect back to the messages detail view
		return HttpResponseRedirect('/webmaster/messages')
    
	# Invalid params
	else:
		logger.error('Invalid Form: %s' % 'MessageDeleteForm')
		
	# If a request made it this far, its a bad one, send back
	# to the messages view
	return HttpResponseRedirect('/webmaster/messages')
    
	

