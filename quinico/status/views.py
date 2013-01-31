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


"""This module contains all of the views for the Quinico Status
   application

"""


import datetime
import logging
import sys
import csv

from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from quinico.webmaster.models import API_Calls as webmaster_calls
from quinico.webmaster.models import API_Errors as webmaster_errors
from quinico.keyword_rank.models import API_Calls as keyword_rank_calls
from quinico.keyword_rank.models import API_Errors as keyword_rank_errors
from quinico.webpagetest.models import API_Calls as webpagetest_calls
from quinico.webpagetest.models import API_Errors as webpagetest_errors
from quinico.pagespeed.models import API_Calls as pagespeed_calls
from quinico.pagespeed.models import API_Errors as pagespeed_errors
from quinico.seomoz.models import API_Calls as seomoz_calls
from quinico.seomoz.models import API_Errors as seomoz_errors
from quinico.status.forms import APIStatusForm
from django.db.models import Sum


# Get an instance of a logger
logger = logging.getLogger(__name__)


# API Status Index Page
def api(request):
    """API Status View
    Allow graphing of API calls/errors over time

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = APIStatusForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            date_to = form.cleaned_data['date_to']
            date_from = form.cleaned_data['date_from']
            api = form.cleaned_data['api']
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

	    # Obtain the API Calls and Errors
	    # Convert the input api name into the appropriate calls/errors class
	    try:
		ca = getattr(sys.modules[__name__],(api + '_calls'))
		er = getattr(sys.modules[__name__],(api + '_errors'))
	    except AttributeError as e:
		logger.error(e)
		return render_to_response(
		 'error/error.html',
		  {
		    'title':'Quinico | Error',
		    'error':e
		  },
		  context_instance=RequestContext(request)
		)

	    calls = ca.objects.filter(call_date__range=[date_from,date_to]).values('call_date').annotate(Sum('count')).order_by('call_date')
	    errors = er.objects.filter(call_date__range=[date_from,date_to]).values('call_date').annotate(Sum('count')).order_by('call_date')


	    # Put the data together for the template
	    # Use calls as the reference
	    data = []
	    for call in calls:
		row = []
		row.append(call['call_date'])
		row.append(call['count__sum'])
		
		# See if there is an equivalent date in errors
		error_match = 0
		for error in errors:
		    if error['call_date'] == call['call_date']:
			error_match = 1
			row.append(error['count__sum'])

		if not error_match:
		    row.append('0')

		# Add the row
		data.append(row)

	    # If there is no data let the user know
	    if not data:
	       message = 'The report returned no data.'
	       return render_to_response(
		   'misc/generic.html',
		   {
		    'title':'Quinico | No Data',
		    'message':message
		   },
		   context_instance=RequestContext(request)
		)

	    # Construct the dashboard, download and monitoring links
	    csv_link = 'http://%s/status/api?api=%s&format=csv' % (request.META['HTTP_HOST'],api)

	    # Setup 'friendly' names for the apis
	    friendly_names = {
			      'keyword_rank':'Google Search API',
			      'pagespeed':'Google Pagespeed API',
			      'webmaster':'Google Webmaster API',
			      'seomoz':'SEOMoz API',
			      'webpagetest':'Webpagetest API'
			     }

	    # Print the page

	    # If this is a request for special formatting, give it, otherwise give everything
	    if format:
		# CSV download (there is no template for this)
		if request.GET['format'] == 'csv':
		    response = HttpResponse(mimetype='text/csv')
		    response['Content-Disposition'] = 'attachment;filename=quinico_data.csv'
		    writer = csv.writer(response)
		    writer.writerow(['date','calls','errors'])
		    for row in data:
			writer.writerow(row)
		    return response

	    # Just a standard HTML response is being requested
	    else:
		return render_to_response(
		 'status/api.html',
		  {
		   'title':'Quinico | API Status',
		   'api':friendly_names[api],
		   'data':data,
		   'csv_link':csv_link
		  },
		  context_instance=RequestContext(request)
		)

    # Ok, its not a form submit
    else:
        form = APIStatusForm()

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Print the page
    return render_to_response(
       'status/api_index.html',
       {
          'title':'Quinico | API Status',
          'form':form,
          'date_from':date_from,
          'date_to':date_to
       },
       context_instance=RequestContext(request)
    )

