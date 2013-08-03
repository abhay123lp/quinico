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


"""This module contains all of the views for the Quinico Webpagetest
   application

"""


import datetime
import logging
import urllib
import csv
import pytz
from django.db.models import Avg
from django.utils import simplejson
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from quinico.main.models import Config
from quinico.webpagetest.models import Test
from quinico.webpagetest.models import Score
from quinico.webpagetest.forms import WebpagetestHistoryForm
from quinico.webpagetest.forms import WebpagetestReportForm
from quinico.webpagetest.forms import WebpagetestTrendForm
from quinico.dashboard.models import Dash_Settings


# Get an instance of a logger
logger = logging.getLogger(__name__)


def report(request):
    """Webpagetest Report View
    Provide the full Webpagtest raw XML report
    """

    form = WebpagetestReportForm(request.GET)
    if form.is_valid():
        id = form.cleaned_data['id']

        # Obtain the report download location
        report_path = Config.objects.filter(config_name='report_path').values('config_value')[0]['config_value']

        # Obtain the report name
        details = Score.objects.filter(id=id).values('test_id','report')

        # Report
        report = details[0]['report']

        # Load the file
        try:
            # Load the file
            xml_file = open('%s/%s' % (report_path,report))
            x = xml_file.read()
        except:
            # Give the error page
            return render_to_response(
               'error/error.html',    
               {   
                  'title':'Quinico | Error',
                  'error':'File not found:%s/%s' % (report_path,report)
               },  
               context_instance=RequestContext(request)
            )         

        # Close the file
        xml_file.close()

        # Give the XML response
        return HttpResponse(x,mimetype="application/xml")

    # Invalid request, give them the error page
    else:
        # Print the page
        return render_to_response(
           'error/error.html',
           {
              'title':'Quinico | Error',
              'error':'Invalid request',
       },
       context_instance=RequestContext(request)
    )


def trends(request):
    """Webpagetest Trends View
    Allow graphing of individual Webpagetest metrics over time

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = WebpagetestTrendForm(request.GET)

        if form.is_valid():

            # Obtain the cleaned data
            test_id = form.cleaned_data['test_id']
            date_to = form.cleaned_data['date_to']
            date_from = form.cleaned_data['date_from']
            metric = form.cleaned_data['metric']
            include_failed = form.cleaned_data['include_failed']
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

            # The dates were already set, convert them to strings
            else:
                date_to = date_to.strftime("%Y-%m-%d")
                date_from = date_from.strftime("%Y-%m-%d")

            # Add time information to the dates and the timezone (use the server's timezone)
            date_from = date_from
            date_from += ' 00:00:00'
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
            date_from = pytz.timezone(settings.TIME_ZONE).localize(date_from)

            date_to = date_to
            date_to += ' 23:59:59'
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S')
            date_to = pytz.timezone(settings.TIME_ZONE).localize(date_to)


            # Obtain the domain, url and location for the chart display
            test = Test.objects.filter(id=test_id)

            if include_failed:
                test_failed = 1
            else:
                test_failed = 0

    	    # Obtain the scores for this test
            scores1 = Score.objects.filter(test_id=test_id,
                                           date__range=[date_from,date_to],
                                           viewNumber='1',
                                           test_failed__lte=test_failed,
                                        ).extra({'date':"date(convert_tz(date,'%s','%s'))" % ('UTC',settings.TIME_ZONE)}
                                        ).values('date').annotate(Avg(metric)).order_by('date')

            logger.debug(scores1.query)
            logger.debug(scores1)

    	    # Obtain the scores for this test
            scores2 = Score.objects.filter(test_id=test_id,
                                           date__range=[date_from,date_to],
                                           viewNumber='2',
                                           test_failed__lte=test_failed,
                                         ).extra({'date':"date(convert_tz(date,'%s','%s'))" % ('UTC',settings.TIME_ZONE)}
                                         ).values('date').annotate(Avg(metric)).order_by('date')

            logger.debug(scores2.query)
            logger.debug(scores2)

    	    # Put the data together so its easier to manipulate in the template
    	    # like this: scores[{'date':'2012-01-01','view1':'4023',view2':'321'}]
            scores = []

    	    # We'll always have two views for every date because the data job will just enter zeroes
            # if one view fails
            for i in range(len(scores1)):
                # Create a new dict for each date.
                dict = {'date':scores1[i]['date'],'view1':scores1[i]['%s__avg' % metric],'view2':scores2[i]['%s__avg' % metric]}

                # Push onto the main scores array
                scores.append(dict)

            logger.debug(scores)

    	    # Construct the dashboard, download and monitoring links
            base_url = 'http://%s/webpagetest/trends?' % (request.META['HTTP_HOST'])
            db_link = '%stest_id=%s&metric=%s&format=db' % (base_url,test_id,metric)
            json_link = '%stest_id=%s&metric=%s&format=json' % (base_url,test_id,metric)

    	    # Print the page
                
    	    # If this is a request for special formatting, give it, otherwise give everything
            if format:
                # JSON request
                if format == 'json':
                    return HttpResponse(simplejson.dumps([{'date': row['date'].strftime("%Y-%m-%d"),
                                                           'view1': str(row['view1']),
                                                           'view2': str(row['view2'])} for row in scores]),
                                            mimetype="application/json")

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
                        'webpagetest/trends-db.html',
        		      {
                        'title':'Quinico | Webpagetest Trends',
                        'metric':metric,
                        'test':test,
                        'scores':scores,
                        'dash_settings':dash_settings,
                        'width':width,
                        'height':height,
                        'step':step
        		      },
                        context_instance=RequestContext(request)
        		    )

            # Just a standard HTML response is being requested
            else:
                return render_to_response(
                    'webpagetest/trends.html',
        		   {
                    'title':'Quinico | Webpagetest Trends',
                    'metric':metric,
                    'test':test,
                    'scores':scores,
                    'db_link':db_link,
                    'json_link':json_link
        		   },
        		   context_instance=RequestContext(request)
        		)

        else:
            # Invalid form submit
            logger.error('Invalid form: WebpagetestTrendForm: %s' % form.errors)

    # Its not a form submit, or its a failed form submit
    else:
        form = WebpagetestTrendForm()

    # Obtain the test list
    tests = Test.objects.all()

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Print the page
    return render_to_response(
       'webpagetest/trends_index.html',
       {
          'title':'Quinico | Webpagetest Trends',
          'form':form,
          'tests':tests,
          'date_from':date_from,
          'date_to':date_to
       },
       context_instance=RequestContext(request)
    )


def history(request):
    """Webpagetest History View
    Allow presentation of raw webpagetest data for a defined time range

    """

    # If request.GET is empty, show the index, otherwise validate
    # the form and provide the results

    if request.GET:
        # Check the form elements
        form = WebpagetestHistoryForm(request.GET)

        if form.is_valid():
            # Obtain the cleaned data
            test_id = form.cleaned_data['test_id']
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

            # The dates were already set, convert them to strings
            else:
                date_to = date_to.strftime("%Y-%m-%d")
                date_from = date_from.strftime("%Y-%m-%d")


    	    # Obtain the domain, url and location for the chart display
    	    test = Test.objects.filter(id=test_id)

    	    # Values that we'll export in CSV
    	    headings = ['date','viewNumber','loadTime','ttfb','bytesOut','bytesOutDoc',
    			        'bytesIn','bytesInDoc','requests','requestsDoc','render',
    			        'fullyLoaded','docTime','score_cache','score_cdn','score_gzip',
                        'view_failed','test_failed','testId']

    	    # Construct the csv link
            base_url = 'http://%s/webpagetest/history' % (request.META['HTTP_HOST'])
    	    csv_link = '%s?test_id=%s&date_from=%s&date_to=%s&format=csv' % (base_url,test_id,date_from,date_to)

    	    # Add time information to the dates and the timezone (use the server's timezone)
    	    date_from += ' 00:00:00'
    	    date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
    	    date_from = pytz.timezone(settings.TIME_ZONE).localize(date_from)

    	    date_to += ' 23:59:59'
    	    date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S')
    	    date_to = pytz.timezone(settings.TIME_ZONE).localize(date_to)

    	    # Obtain the data
    	    dates = Score.objects.filter(test_id=test_id,date__range=[date_from,date_to]).values().order_by('-date')


    	    # Print the page

    	    # If this is a request for special formatting, give it, otherwise give everything
    	    # Dashboard request
    	    if format:
    		
                # CSV download (there is no template for this)
                if format == 'csv':
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
        		   'webpagetest/history.html',
        		   {
        		      'title':'Quinico | Webpagetest History',
        		      'test':test,
        		      'dates':dates,
        		      'csv_link':csv_link
        		   },
        		   context_instance=RequestContext(request)
        		)

        else:
            # Invalid form submit
            logger.error('Invalid form: WebpagetestHistoryForm: %s' % form.errors)

    # Its not a form submit, or its a failed form submit
    else:
        form = WebpagetestHistoryForm()

    # Obtain the test list
    tests = Test.objects.all()

    # Obtain the current date for the to date field
    now = datetime.datetime.today()
    date_to = now.strftime("%Y-%m-%d")

    # Move back 30 days
    then = datetime.timedelta(days=30)
    date_from = now - then
    date_from = date_from.strftime("%Y-%m-%d")

    # Print the page
    return render_to_response(
       'webpagetest/history_index.html',
       {
          'title':'Quinico | Webpagetest History',
          'form':form,
          'tests':tests,
          'date_from':date_from,
          'date_to':date_to
       },
       context_instance=RequestContext(request)
    )


