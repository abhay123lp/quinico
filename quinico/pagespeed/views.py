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


"""This module contains all of the views for the Quinico Pagespeed
   application

"""


import datetime
import json
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
from quinico.pagespeed.models import Domain
from quinico.pagespeed.models import Score
from quinico.pagespeed.models import Test
from quinico.pagespeed.models import Url
from quinico.pagespeed.forms import PagespeedBreakdownForm
from quinico.pagespeed.forms import PagespeedHistoryForm
from quinico.pagespeed.forms import PagespeedReportForm
from quinico.pagespeed.forms import PagespeedTrendForm
from quinico.dashboard.models import Dash_Settings


# Get an instance of a logger
logger = logging.getLogger(__name__)


def report(request):
    """Pagespeed Report View
    Provide the full Pagespeed report
    """

    form = PagespeedReportForm(request.GET)
    if form.is_valid():
        id = form.cleaned_data['id']

        # Obtain the report download location
        report_path = Config.objects.filter(config_name='report_path').values('config_value')[0]['config_value']

        # Obtain the report name
        details = Score.objects.filter(id=id).values('test_id','date','strategy','report')

        # Domain and URL
        domain = Test.objects.filter(id=details[0]['test_id']).values('domain_id__domain','url_id__url')

        # Date
        date = details[0]['date']

        # Strategy
        strategy = details[0]['strategy']

        # Report
        report = details[0]['report']
 
        try:
            # Load the file
            json_file = open('%s/%s' % (report_path,report))
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

        # Deserialize it
        json_data = json.load(json_file)

        # Close the file
        json_file.close()

        # Report Results for the template, in this format
        data = []
        # data[{
        #       name: 'AvoidCssImport'
        #       formattedName: 'Avoid CSS @import',
        #       score: 100,
        #       impact: 0.1,
        #       color: 'red',
        #       urls: [
        #              {
        #               header: 'The following external stylesheets were included in http://www.foo.bar',
        #		urls: [
        #                      'http://www.foo.bar',
        #                      'http://www.clown.com
  	    #		      ]
        #              }
        #	      ]
        #      }
        #     ]
        #

        # Manipulate the data so its easier to provide in the template
        for result in json_data['formattedResults']['ruleResults']:
            # Create a temporary structure to hold this result
            data_tmp = {}
            data_tmp['name'] = result
            data_tmp['formattedName'] = json_data['formattedResults']['ruleResults'][result]['localizedRuleName']
            data_tmp['score'] = json_data['formattedResults']['ruleResults'][result]['ruleScore']
            data_tmp['impact'] = json_data['formattedResults']['ruleResults'][result]['ruleImpact']
 
            if data_tmp['impact'] >= 10:
                data_tmp['color'] = '#F62217'
            elif data_tmp['impact'] < 10 and data_tmp['impact'] >= 2:
                data_tmp['color'] = '#FF9900'
            else:
                data_tmp['color'] = '#6699FF'

            if 'urlBlocks' in json_data['formattedResults']['ruleResults'][result]:
                
                # We've got some URLs so create an array to hold them
                data_tmp['urls'] = []

                for block in json_data['formattedResults']['ruleResults'][result]['urlBlocks']:

                    # Each block will have its own dict
                    block_tmp = {}

                    ## First the Header ##

                    # The optimization, in human readable form
                    header = block['header']['format']

                    # If there are args, then we need to interpolate them in
                    if 'args' in block['header']:
                        for counter,item in enumerate(block['header']['args'],start=1):
                            header = header.replace('$%s' % counter,item['value'])

                    # Add the header
                    block_tmp['header'] = header

                    ## Now the Urls ##

                    # First see if there are urls
                    if 'urls' in block:

                        urls_tmp = []

                        for url in block['urls']:
                            url_format = url['result']['format']

                            # Now see if we need to interpolate
                            if 'args' in url['result']:
                                for counter,item in enumerate(url['result']['args'],start=1):
                                    url_format = url_format.replace('$%s' % counter,item['value'])

                            urls_tmp.append(url_format)

                        # Add the url data
                        block_tmp['urls'] = urls_tmp

                    # Add the block data
                    data_tmp['urls'].append(block_tmp) 

            # Add the tmp data structure
            data.append(data_tmp)        

        # Print the page
        return render_to_response(
           'pagespeed/report.html',               
           {
              'title':'Quinico | Pagespeed Report',
              'date':date,
              'domain':domain[0]['domain_id__domain'],
              'url':domain[0]['url_id__url'],
              'strategy':strategy,
              'report':data,
       },
       context_instance=RequestContext(request)
    )

    # Invalid request, give them the error page
    else:
        # Give the error page
        return render_to_response(
           'error/error.html',               
           {
              'title':'Quinico | Error',
              'error':'Invalid request',
           },
           context_instance=RequestContext(request)
        )


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
            # We need to keep the originals unchanged for the CSV link
            date_from_tz = date_from
            date_from_tz += ' 00:00:00'
            date_from_tz = datetime.datetime.strptime(date_from_tz, '%Y-%m-%d %H:%M:%S')
            date_from_tz = pytz.timezone(settings.TIME_ZONE).localize(date_from_tz)

            date_to_tz = date_to
            date_to_tz += ' 23:59:59'
            date_to_tz = datetime.datetime.strptime(date_to_tz, '%Y-%m-%d %H:%M:%S')
            date_to_tz = pytz.timezone(settings.TIME_ZONE).localize(date_to_tz)

    	    # Unquote the url to UTF-8 and then decode
    	    u_unenc = urllib.unquote(url.encode('utf-8')).decode('utf-8')

    	    # Obtain the scores for this test
            # Convert the times to the server timezone first and then take the date portion
    	    scores = Score.objects.filter(test_id__domain__domain=domain,
                                          test_id__url__url=u_unenc,
                                          date__range=[date_from_tz,date_to_tz],
                                          strategy=strategy
                                         ).extra({'date':"date(convert_tz(date,'%s','%s'))" % ('UTC',settings.TIME_ZONE)}
                                         ).values('date').annotate(Avg(metric)).order_by('date')

            logger.debug(scores.query)
            logger.debug(scores)

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
                    return HttpResponse(simplejson.dumps([{'date': row['date'].strftime("%Y-%m-%d"),metric: row['%s__avg' % metric]} for row in scores]),mimetype="application/json")

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
                    for row in scores:
                        writer.writerow([row['date'].strftime("%Y-%m-%d"),row['%s__avg' % metric]])
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
        else:
            # Invalid form submit
            logger.error('Invalid form: PagespeedTrendForm: %s' % form.errors)

    # Its not a form submit, or its a failed form submit
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
            width = form.cleaned_data['width']
            height = form.cleaned_data['height']

    	    # Unquote the url to UTF-8 and then decode
    	    u_unenc = urllib.unquote(url.encode('utf-8')).decode('utf-8')

    	    # If the date is missing, set it b/c this is probably
    	    # an API or DB request (just give the most recent)
            if not date:
                last_run = Score.objects.filter(test_id__domain__domain=domain,
                                                test_id__url__url=u_unenc,
                                                strategy=strategy
                                               ).values('date').order_by('-date')[:1]
    	   
                if last_run[0]['date']:
                    date = last_run[0]['date']

                    # Convert from UTC to our timezone
                    date = date.astimezone(pytz.timezone(settings.TIME_ZONE))

                # Looks like the pagespeed job has never been run
                else:
                    message = 'The report returned no data.  It appears the Pagespeed data job has never been run'
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

            # DJango does not give us an easy way to match on the date of a datetime, so we'll do a range between
            # 00:00:00 and 23:59:59
            # From/To dates will be variants of the existing date 
            # date is currently in the form Y-m-d

            # Format the datetime as a date string - this will be the starting point for the from/to dates
            date = date.strftime('%Y-%m-%d')
            d_from = date
            d_to = date

            # Create forward/backward links for navigation if this is not an API request
            if not format:
                # The reference date will be the given date, or the last run date
                ref_date = datetime.datetime.strptime(date,'%Y-%m-%d')
                date_back = (ref_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                back_link = '/pagespeed/breakdown?domain=%s&url=%s&strategy=%s&date=%s' % (domain,url,strategy,date_back)
                date_forward = (ref_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                forward_link = '/pagespeed/breakdown?domain=%s&url=%s&strategy=%s&date=%s' % (domain,url,strategy,date_forward)

            # Make the from date the beginning of the day
            # Convert back to a datetime
            # Add our timezone
            d_from += ' 00:00:00'
            d_from = datetime.datetime.strptime(d_from,'%Y-%m-%d %H:%M:%S')
            d_from = pytz.timezone(settings.TIME_ZONE).localize(d_from)

            d_to += ' 23:59:59'
            d_to = datetime.datetime.strptime(d_to,'%Y-%m-%d %H:%M:%S')
            d_to = pytz.timezone(settings.TIME_ZONE).localize(d_to)

            scores = Score.objects.filter(test_id__domain__domain=domain,
                                          test_id__url__url=u_unenc,
                                          date__range=[d_from,d_to],
                                          strategy=strategy,
                                         ).extra({'date':"date(convert_tz(date,'%s','%s'))" % ('UTC',settings.TIME_ZONE)}
                                         ).values('date').annotate(
    					                   Avg('numberResources'),
    					                   Avg('numberStaticResources'),
    					                   Avg('numberCssResources'),
    					                   Avg('totalRequestBytes'),
    					                   Avg('textResponseBytes'),
    					                   Avg('cssResponseBytes'),
    					                   Avg('htmlResponseBytes'),
    					                   Avg('imageResponseBytes'),
    					                   Avg('javascriptResponseBytes'),
    					                   Avg('otherResponseBytes')
    					                  )

            logger.debug(scores.query)
            logger.debug(scores)

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
            db_link2 = '%s=%s&url=%s&strategy=%s&format=db2' % (base_url,domain,url,strategy)
            json_link = '%s=%s&url=%s&strategy=%s&format=json' % (base_url,domain,url,strategy)

    	    # Print the page

    	    # If this is a request for special formatting, give it, otherwise give everything
            if format:
                # JSON request
                if format == 'json':
                    return HttpResponse(simplejson.dumps([{
                                                           'date': row['date'].strftime("%Y-%m-%d"),
                                                           'numberResources': row['numberResources__avg'],
                                                           'numberstatisResources': row['numberStaticResources__avg'],
                                                           'numberCssResources': row['numberCssResources__avg'],
                                                           'totalRequestBytes': row['totalRequestBytes__avg'],
                                                           'textResponseBytes': row['textResponseBytes__avg'],
                                                           'cssResponseBytes': row['cssResponseBytes__avg'],
                                                           'htmlResponseBytes': row['htmlResponseBytes__avg'],
                                                           'imageResponsebytes': row['imageResponseBytes__avg'],
                                                           'javascriptResponseBytes': row['javascriptResponseBytes__avg'],
                                                           'otherResponseBytes': row['otherResponseBytes__avg']
                                                          } for row in scores]),
                                                          mimetype="application/json")
                
                # Dashboard request
                elif format == 'db2':
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
                        'pagespeed/breakdown-db2.html',
        		      {
            			'title':'Quinico | Pagespeed Breakdown',
            			'date':date,
            			'domain':domain,
            			'url':u_unenc,
            			'strategy':strategy,
            			'scores':scores,
            			'dash_settings':dash_settings,
                        'width':width,
                        'height':height,
            		   },
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
        		      'db_link2':db_link2,
        		      'json_link':json_link,
        		   },
        		   context_instance=RequestContext(request)
        		)

        else:
            # Invalid form submit
            logger.error('Invalid form: PagespeedBreakdownForm: %s' % form.errors)

    # Its not a form submit, or its a failed form submit
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

            # The dates were already set, convert them to strings
            else:
                date_to = date_to.strftime("%Y-%m-%d")
                date_from = date_from.strftime("%Y-%m-%d")

    	    # Unquote the url to UTF-8 and then decode
    	    u_unenc = urllib.unquote(url.encode('utf-8')).decode('utf-8')

    	    # Values that we'll export in CSV
    	    headings = ['date','score','numberHosts','numberResources','numberStaticResources','numberCssResources',
    			        'totalRequestBytes','textResponseBytes','cssResponseBytes','htmlResponseBytes','imageResponseBytes',
    			        'javascriptResponseBytes','otherResponseBytes']

            # Construct the csv link
            base_url = 'http://%s/pagespeed/history?domain=%s' % (request.META['HTTP_HOST'],domain)
            csv_link = '%s&url=%s&strategy=%s&date_from=%s&date_to=%s&format=csv' % (base_url,url,strategy,date_from,date_to)

            # Add time information to the dates and the timezone (use the server's timezone)
            date_from += ' 00:00:00'
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
            date_from = pytz.timezone(settings.TIME_ZONE).localize(date_from)

            date_to += ' 23:59:59'
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S')
            date_to = pytz.timezone(settings.TIME_ZONE).localize(date_to)

    	    # Obtain the data
    	    dates = Score.objects.filter(test_id__domain__domain=domain,
                                             test_id__url__url=u_unenc,
                                             date__range=[date_from,date_to],
                                             strategy=strategy
                                            ).values().order_by('-date')


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

        else:
            # Invalid form submit
            logger.error('Invalid form: PagespeedHistoryForm: %s' % form.errors)

    # Its not a form submit, or its a failed form submit
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

