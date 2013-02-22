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


"""This module contains all of the views for the Quinico Keyword Rank
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
from quinico.main.models import Config
from quinico.keyword_rank.models import Domain
from quinico.keyword_rank.models import Keyword
from quinico.keyword_rank.models import Rank
from quinico.keyword_rank.models import Top_Ten
from quinico.keyword_rank.models import Test
from quinico.keyword_rank.forms import UploadForm
from quinico.keyword_rank.forms import KeywordDashboardForm
from quinico.keyword_rank.forms import KeywordTrendForm
from quinico.dashboard.models import Dash_Settings
from django.contrib.admin.views.decorators import staff_member_required


# Get an instance of a logger
logger = logging.getLogger(__name__)


@staff_member_required
def upload(request):
    """Upload CSV of Keywords
    Allow upload of keywords through the DJango admin
    User must be authenticated

    """

    # Obtain the domain list
    domains = Domain.objects.all().order_by('domain')

    if request.method == "POST":
        upload_form = UploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            upload_form.save()

    else:
        # Display the upload form
        upload_form = UploadForm()

    # Print the page
    return render_to_response(
       'keyword_rank/upload.html',
       {
          'title':'Quinico | Keyword Upload',
          'domains':domains,
          'upload_form':upload_form
       },
       context_instance=RequestContext(request)
    )


def trends(request):
    """Keyword Rank Trends View
    Allow graphing of individual keyword ranks over time
 
    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    request.encoding = 'utf-8'

    if request.GET:
        # Check the form elements
        form = KeywordTrendForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            keyword = form.cleaned_data['keyword']
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

            # Obtain the keyword ranks for this keyword and domain
            ranks = Rank.objects.filter(domain__domain=domain,
                                        keyword__keyword=keyword,
                                        date__range=[date_from,date_to]
                                       ).values('date','rank').order_by('date')

            # How many were returned
            dates = len(ranks)
            dates_b = dates - 1

            # Obtain the last one in the query set
            last_date = ranks[dates_b:dates]

            # Obtain the top ten ranks for this keyword
            top_ten = Top_Ten.objects.filter(domain__domain=domain,
                                             keyword__keyword=keyword,
                                             date=last_date[0]['date']
                                            ).values('rank','url__url').order_by('rank')

            # Construct the dashboard, download and monitoring links

            # Add percent encoding to the keyword
            keyword_enc = urllib.quote_plus(keyword.encode('utf-8'))
            base_url = 'http://%s/keyword_rank/trends?domain' % request.META['HTTP_HOST']
            db_link = '%s=%s&keyword=%s&format=db' % (base_url,domain,keyword_enc)
            json_link = '%s=%s&keyword=%s&format=json' % (base_url,domain,keyword_enc)
            csv_link = '%s=%s&keyword=%s&date_from=%s&date_to=%s&format=csv' % (base_url,domain,keyword_enc,date_from,date_to)

            # Print the page

            # If this is a request for special formatting, give it, otherwise give everything
            if format:
                # JSON request
                if format == 'json':
                    return HttpResponse(simplejson.dumps([{'date': row['date'].strftime("%Y-%m-%d"),
                                                           'rank': row['rank']} for row in ranks]),
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
                     'keyword_rank/trends-db.html',
                      {
                        'title':'Quinico | Keyword Trends',
                        'domain_name':domain,
                        'keyword_name':keyword,
                        'ranks':ranks,
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
                    writer.writerow(['date','rank'])
                    for rank in ranks:
                        writer.writerow([rank['date'],rank['rank']])
                    return response

            # Just a standard HTML response is being requested
            else:
                # Obtain the Google gl and googlehost params for display
                country = Domain.objects.filter(domain=domain).values('gl','googlehost')

                return render_to_response(
                 'keyword_rank/trends.html',
                  {
                    'title':'Quinico | Keyword Trends',
                    'domain_name':domain,
                    'country':country,
                    'keyword_name':keyword,
                    'ranks':ranks,
                    'top_ten':top_ten,
                    'db_link':db_link,
                    'json_link':json_link,
                    'csv_link':csv_link
                  },
                  context_instance=RequestContext(request)
                )

    # Ok, its not a form submit
    else:
        form = KeywordTrendForm()

    # Create a dictionary of all domains and keywords
    # to pass to the template so we can create the javascript to 
    # dynamically populate the dropdowns
    kw_dict = {}
    
    # Obtain the domain list
    domain_list = Domain.objects.all()

    # Populate keywords for each domain
    for d in domain_list:
        # Obtain the keyword list
        keyword_list = Test.objects.filter(domain__domain=d).values('keyword__keyword').order_by('keyword__keyword')

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
       'keyword_rank/trends_index.html',               
       {
          'title':'Quinico | Keyword Trends',
          'form':form,
          'list':kw_dict,
          'date_to':date_to,
          'date_from':date_from
       },
       context_instance=RequestContext(request)
    )



def dashboard(request):
    """Keyword Rank Dashboard View
    Provide all relevant keyword information for a specific domain
 
    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
       # Check the form elements
        form = KeywordDashboardForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            domain = form.cleaned_data['domain']
            format = form.cleaned_data['format']

	    # Obtain all of the keywords for this domain
	    # This will be the definitive source
	    keyword_list = Test.objects.filter(domain__domain=domain).values('keyword__keyword')

	    # Setup an empty dictionary to hold the ranks, of the following form: {'keyword':[rank1,rank2,...]}
	    ranks = {}

	    # Setup a dictionary for first page ranks, of the following form in order to keep the dates in order: [{'date':'counter'}]
	    first_page = []

	    # Setup a dictionary for headings on the daily keyword results table
	    headings = {}
	    headings = ['Keyword','Url']

	    # Setup a lookup table for the up/down/unch dates
	    updown_dates = []

	    # Setup the dates that we'll check ranks for
	    numbers = [
		     0,	# Today
		     1,	# Yesterday
		     2,	# Two days ago
		     7,	# Seven days ago
		     14	# Fourteen days ago
		    ]

	    # Run through the dates and compile the data

	    # First, determine when the last time we collected data was
            # If never, then stop here
	    last_run = Rank.objects.values('date').distinct().order_by('-date')[:1]
	    if not last_run:
                return render_to_response(
                 'error/nodata.html',
                  {
                    'title':'Quinico | No Data',
                    'type':'keyword_rank'
                  },
                  context_instance=RequestContext(request)
                )

	    now = datetime.date.today()

	    # If the last run is older than today (usually when data has not been collected for today yet), then shift
	    days = 0
	    if (last_run[0]['date'] == now):
		logger.debug('Last run of keyword_rank data collection was today')
	    if (last_run[0]['date'] < now):
		logger.debug('Last run of keyword_rank data collection happened before today')
		days = (now - last_run[0]['date']).days
		logger.debug('Last run of keyword_rank was %s days ago' % days)

	    for number in numbers:
		logger.debug('Acquiring data for %s days ago' % (number + days))
		then = datetime.timedelta(days=(number + days))
		current_date = now - then
		current_date = current_date.strftime("%Y-%m-%d")
		logger.debug('Formatted date: %s' % current_date)

		# Counter for 1st page ranks
		first_page_counter = 0

		# Add the formatted date to our headings
		headings.append(current_date)
		updown_dates.append(current_date)

		# Request all keywords and ranks for this date
		ranks_date = Rank.objects.filter(domain__domain=domain,date=current_date).values('keyword__keyword','rank','url__url')

		# Look at each keyword and see if we have a result, otherwise set to 'n/a'
		for k in keyword_list:

		    found = 0

		    # Add an empty keyword dict to our dict if its not already there
		    if not k['keyword__keyword'] in ranks:
			ranks[k['keyword__keyword']] = []

		    # Check every rank result for this date for our keyword
		    for r in ranks_date:
			# If this is our keyword, save the rank
			if k['keyword__keyword'] == r['keyword__keyword']:
			    found = 1 
			    # If this is the first day, add the URL first
			    if number == 0:
				ranks[k['keyword__keyword']].append(r['url__url'])
				ranks[k['keyword__keyword']].append(r['rank'])
				# If its on the first page of results, count it
				if r['rank'] > 0 and r['rank'] <= 10:
				    first_page_counter += 1
			    else:
				ranks[k['keyword__keyword']].append(r['rank'])
				# If its on the first page of results, count it
				if r['rank'] > 0 and r['rank'] <= 10:
				    first_page_counter += 1

		    # If we didn't find a result, set to 'n/a'
		    if found != 1:
			if number == 0:
			    ranks[k['keyword__keyword']].append('n/a')
			    ranks[k['keyword__keyword']].append('n/a')
			else:
			    ranks[k['keyword__keyword']].append('n/a')

		# Add the first page ranks
		first_page.append({current_date:first_page_counter})


	    # Compile the position change numbers
	    # If the current day is not available, then these will
	    # all be blank.

	    # Dictionary to hold the up/down/unch numbers
	    changes = {}

	    for keyword in ranks:

		# Skip the last one since we don't have a previous one to compare it to
		# Also note that the first entry in the ranks array is the url so need to account for that
		for day in range(len(ranks[keyword]) - 2):

		    up = 0    # Improved
		    down = 0  # Declined
		    unch = 0  # Unchanged

		    # Did it go up or down between the most recent day and the date in question?
		    # Current day (remember that position 0 is the url)
		    current_day = ranks[keyword][1]

		    # Previous day (skip ahead 2.  The url and the first day
		    previous_day = ranks[keyword][day + 2]

		    # If the current day or previous day is 'n/a', then skip this one
		    if current_day == 'n/a':
			continue

		    if previous_day == 'n/a':
			continue

		    # Nothing changed
		    if current_day == previous_day:
			unch += 1

		    # In the case where the current day is zero but the previous day had a rank
		    # then the rank actually declined (assuming the user did not change the allowable rank results)
		    elif current_day == 0:
			if previous_day > 0:
			    down += 1

		    # In the case where the previous day is zero but the current day has a rank
		    # then the rank actually improved (assuming the user did not change the allowable rank results)
		    elif previous_day == 0:
			if current_day > 0:
			    up += 1

		    # Rank declined
		    elif current_day > previous_day:
			down += 1

		    # Rank improved
		    elif current_day < previous_day:
			up += 1

		    # Add to our list
		    if not updown_dates[day + 1] in changes:
		       changes[updown_dates[day + 1]] = {'up':0,'down':0,'unch':0}

		    changes[updown_dates[day + 1]]['up'] += up
		    changes[updown_dates[day + 1]]['down'] += down
		    changes[updown_dates[day + 1]]['unch'] += unch

	    # Sort the changes list b/c it will be out of order
	    changes = sorted(changes.items(), reverse=True)

	    # Obtain a count of all keywords
	    keyword_count = Test.objects.filter(domain__domain=domain).values('keyword__keyword').count()

	    # Obtain the country that the results are coming from
	    country = Domain.objects.filter(domain=domain).values('gl','googlehost')

	    # Construct the dashboard, download and monitoring links
            base_url = 'http://%s/keyword_rank/dashboard?domain' % (request.META['HTTP_HOST'])
	    db_link = '%s=%s&format=db' % (base_url,domain)
	    db_link1 = '%s=%s&format=db1' % (base_url,domain)
	    json_link1 = '%s=%s&format=json1' % (base_url,domain)
	    json_link2 = '%s=%s&format=json2' % (base_url,domain)
	    csv_link = '%s=%s&format=csv' % (base_url,domain)

	    # Print the page

	    # If this is a request for special formatting, give it, otherwise give everything
	    if format:
		# JSON request
		# There are two dashboards here:
		# json1 - (Keyword Position Changes)
		# and
		# json2 - First Page Rankings
		if format == 'json1':
                    return HttpResponse(simplejson.dumps([row for row in changes]),
                                        mimetype="application/json")

		if format == 'json2':
                    return HttpResponse(simplejson.dumps([row for row in first_page]),
                                        mimetype="application/json")

		# Dashboard request
		# There are two dashboards here:
		# db - First Page Rankings
		# and
		# db1 - Keyword Position Changes
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
		     'keyword_rank/dashboard-db.html',
		      {
			'title':'Quinico | Keyword Dashboard',
			'domain':domain,
			'country':country,
			'first_page':first_page,
			'dash_settings':dash_settings
		      },
		      mimetype='application/json',
		      context_instance=RequestContext(request)
		    )

		elif format == 'db1': 
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
		     'keyword_rank/dashboard-db1.html',
		      {
			'title':'Quinico | Keyword Dashboard',
			'domain':domain,
			'country':country,
			'changes':changes,
			'dash_settings':dash_settings
		      },
		      context_instance=RequestContext(request)
		    )

		# CSV download (there is no template for this)
		elif format == 'csv':
		    response = HttpResponse(mimetype='text/csv')
		    response['Content-Disposition'] = 'attachment;filename=quinico_data.csv'
		    writer = csv.writer(response)
		    writer.writerow(headings)
		    for rank in ranks:
			writer.writerow([rank.encode('utf-8'),
                                         ranks[rank][0],
                                         ranks[rank][1],
                                         ranks[rank][2],
                                         ranks[rank][3],
                                         ranks[rank][4],
                                         ranks[rank][5]])
		    return response

	    # Just a standard HTML response is being requested
	    else: 
		return render_to_response(
		 'keyword_rank/dashboard.html',
		  {
		    'title':'Quinico | Keyword Dashboard',
		    'domain':domain,
		    'headings':headings,
		    'ranks':ranks,
		    'first_page':first_page,
		    'changes':changes,
		    'keyword_count':keyword_count,
		    'country':country,
		    'db_link':db_link,
		    'db_link1':db_link1,
		    'json_link1':json_link1,
		    'json_link2':json_link2,
		    'csv_link':csv_link
		  },
		  context_instance=RequestContext(request)
		)

    # Ok, its not a form submit
    else:
        form = KeywordDashboardForm()

    # Obtain the domain list
    list = Domain.objects.all().order_by('domain')

    # Print the page
    return render_to_response(
       'keyword_rank/dashboard_index.html',
       {
          'title':'Quinico | Keyword Dashboard',
          'form':form,
          'list':list
       },
       context_instance=RequestContext(request)
    )


