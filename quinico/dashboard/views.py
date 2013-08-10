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


"""This module contains all of the views for the Quinico Dashboard
   application

"""


import logging
import re

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from quinico.main.models import Config
from quinico.dashboard.models import Subscription
from quinico.dashboard.models import Dash_Settings
from quinico.dashboard.models import Url
from quinico.dashboard.models import Url_Subscription
from quinico.dashboard import preferences
from quinico.main.models import Config

# Get an instance of a logger
logger = logging.getLogger(__name__)


@login_required
def admin(request):
    """Dashboard admin page

    If this is a POST, update settings, otherwise give them the index

    """

    if request.method == 'POST':
        # Set the requested attributes and send the user back to the dashboard admin
        if request.user.is_authenticated():
            logger.debug('user %s is authenticated' % request.user.username)

            # Get the user's ID
            user_id = User.objects.filter(username=request.user.username).values('id')

            # Stock dashboard graph subscriptions
            # Check if there is an entry for the user and add one if not with no subscriptions
            sub_exists = Subscription.objects.filter(user__username=request.user.username)
            if not sub_exists:
                Subscription(user_id=user_id[0]['id'],
                             keyword_rank=False,
                             pagespeed=False,
                             webpagetest=False,
                             seomoz=False,
                             webmaster=False
                            ).save()

            # Set the user's top level preferences (start w/ everything false)
            categories = {'keyword_rank':False,'pagespeed':False,'webpagetest':False,'seomoz':False,'webmaster':False}
            for category in categories:
                if category in request.POST and request.POST[category] == 'on':
                    categories[category] = True

            Subscription.objects.filter(user_id=user_id[0]['id']).update(
                                                                         keyword_rank=categories['keyword_rank'],
                                                                         pagespeed=categories['pagespeed'],
                                                                         webpagetest=categories['webpagetest'],
                                                                         seomoz=categories['seomoz'],
                                                                         webmaster=categories['webmaster']
                                                                        )

            # Dashboard Settings
            # Check if there is an entry for the user and add one if not with default settings
            set_exists = Dash_Settings.objects.filter(user__username=request.user.username)

            # User has no custom settings
            if not set_exists:
                Dash_Settings(user_id=user_id[0]['id'],
                              slots=Config.objects.filter(config_name='dashboard_slots').values('config_value')[0]['config_value'],
                              frequency=Config.objects.filter(config_name='dashboard_frequency').values('config_value')[0]['config_value'],
                              width=Config.objects.filter(config_name='dashboard_width').values('config_value')[0]['config_value'],
                              height=Config.objects.filter(config_name='dashboard_height').values('config_value')[0]['config_value'],
                              font=Config.objects.filter(config_name='dashboard_font').values('config_value')[0]['config_value']
                             ).save()

            # User had custom settings, check them
            else:
                # Set the settings to defaults and then check if they have been changed
                dash_set = {'slots':Config.objects.filter(config_name='dashboard_slots').values('config_value')[0]['config_value'],
                            'frequency':Config.objects.filter(config_name='dashboard_frequency').values('config_value')[0]['config_value'],
                            'width':Config.objects.filter(config_name='dashboard_width').values('config_value')[0]['config_value'],
                            'height':Config.objects.filter(config_name='dashboard_height').values('config_value')[0]['config_value'],
                            'font':Config.objects.filter(config_name='dashboard_font').values('config_value')[0]['config_value']}

                for set in dash_set:
                    if set in request.POST and request.POST[set] != '':
                        dash_set[set] = request.POST[set]

                Dash_Settings.objects.filter(user_id=user_id[0]['id']).update(
                                                                         slots=dash_set['slots'],
                                                                         frequency=dash_set['frequency'],
                                                                         width=dash_set['width'],
                                                                         height=dash_set['height'],
                                                                         font=dash_set['font']
                                                                        )

            # Custom URLs
            # Add any Urls the user is requesting
            if 'url' in request.POST:
                for url in request.POST.getlist('url'):
                   # If its an empty one, don't do anything
                   if not url == '':
                       # See if this URL already exists.  If not, add it
                       url_exist = Url.objects.filter(url=url)
                       if not url_exist:
                          # Add it
                          Url(url=url).save()

                       # See if the user is already subscribed
                       url_id = Url.objects.filter(url=url).values('id')[0]['id']
                       user_subscribed = Url_Subscription.objects.filter(user_id=user_id[0]['id'],url_id=url_id)
 
                       if not user_subscribed:
                           # Subscribe the user to it
                           Url_Subscription(user_id=user_id[0]['id'],url_id=url_id).save()


            # Remove any Urls the user is requesting
            # We need to look through all post parameters and match on user_del_number.  
            # Number will be the id to remove
            for key in request.POST:
                match = re.match('url_del_(\d+)',key)
                if not match is None:
                    id = match.group(1)

                    # Get the URL ID in case we are removing it
                    url_id = Url_Subscription.objects.filter(id=id).values('url_id')[0]['url_id']

                    # Remove the subscription
                    Url_Subscription.objects.filter(id=id,user_id=user_id[0]['id']).delete()

                    # If nobody else is subscribed, remove the URL
                    subscribed = Url_Subscription.objects.filter(url_id=url_id)
                    if not subscribed:
                        Url.objects.filter(id=url_id).delete()

            # Send them back
            return HttpResponseRedirect('/dashboard/admin')

        else:
            # Don't save anything b/c a user needs to be logged in to do anything
            return HttpResponseRedirect('/dashboard/admin')
    
    # Its a GET so just print the admin page
    else:
        # If the user is authenticated, show them their stuff,
        # otherwise they are going to be given everything
        if request.user.is_authenticated():
            logger.debug('user %s is authenticated' % request.user.username)

            # Obtain the user's graph subscriptions
            subscription = Subscription.objects.filter(user__username=request.user.username)
        
            # Obtain the user's dashboard settings
            # Should only return a single row
            dash_settings = Dash_Settings.objects.filter(user__username=request.user.username)

            # Obtain the user's custom URL settings
            urls = Url_Subscription.objects.filter(user__username=request.user.username).values('id','url_id__url')
            logger.debug(urls.query)
        
        # Subscribe them to everything and give the defaults
        else:
            subscription = [{'keyword_rank':1,'pagespeed':1,'webpagetest':1,'seomoz':1,'webmaster':1}]
            dash_settings = [{'slots':Config.objects.filter(config_name='dashboard_slots').values('config_value')[0]['config_value'],
                              'frequency':Config.objects.filter(config_name='dashboard_frequency').values('config_value')[0]['config_value'],
                              'width':Config.objects.filter(config_name='dashboard_width').values('config_value')[0]['config_value'],
                              'height':Config.objects.filter(config_name='dashboard_height').values('config_value')[0]['config_value'],
                              'font':Config.objects.filter(config_name='dashboard_font').values('config_value')[0]['config_value']}]
            urls = None
            user = 'anon'

        # Print the page
        return render_to_response(
           'dashboard/admin.html',
           {
              'title':'Dashboard Admin',
              'subscription':subscription,
              'dash_settings':dash_settings,
              'urls':urls
           },
           context_instance=RequestContext(request)
        )


def index(request):
    """Index Page"""

    # If an admin has turned any of the top level reports off, then even if the
    # user is subscribed to them, they will not appear

    # Create a list of URLS and also a reference for which URLs are tables (html) and which
    # are google charts (json) - this will be done in javascript
    # urls = ['url']['type']
    url_list = {}

    # Find out what this user is subscribed to
    subs = None
    if request.user.is_authenticated():
        anonymous = False
        subs = Subscription.objects.filter(user__username=request.user.username).values('keyword_rank',
                                                                                        'pagespeed',
                                                                                        'webpagetest',
                                                                                        'seomoz',
                                                                                        'webmaster')
        logger.debug('user %s subscriptions: %s' % (request.user.username,subs))
    else:
        anonymous = True

    # Instantiate the preferences url_list builder
    prefs = preferences.prefs(logger)

    # Report preferences we'll look for
    report_prefs = ['keyword_rank','pagespeed','webpagetest','seomoz','webmaster']

    for report in report_prefs:

        logger.debug('setting dashboard prefs for %s' % report)

        # Create the url list
        disable_report = int(Config.objects.filter(config_name='disable_%s_reports' % report).values('config_value')[0]['config_value'])

        # If the admin has disabled these reports, they won't be shown
        if disable_report:
            logger.debug('%s reports are disabled and will not be shown in the dashboard' % report)
            # They are disabled, so no reports will be shown
            pass
        # They are not disabled, see if the user subscribed to them 
        elif subs:
            if subs[0][report] == True:
                logger.debug('User is subscribed to %s reports and will receive them in the dashboard' % report)
                method = getattr(prefs,report)
                url_list = method(url_list,request.META['HTTP_HOST'])
        # They are not disabled, if the user is anonymous, give them the reports
        elif anonymous == True:
            logger.debug('User is anonymous and will receive %s reports in the dashboard' % report)
            method = getattr(prefs,report)
            url_list = method(url_list,request.META['HTTP_HOST'])


    # Obtain the user's dashboard preferences
    # Check if there is an entry for the user if not, give them the defaults
    dash_settings = Dash_Settings.objects.filter(user__username=request.user.username)
    if not dash_settings:
        dash_settings = [{'slots':Config.objects.filter(config_name='dashboard_slots').values('config_value')[0]['config_value'],
                          'frequency':Config.objects.filter(config_name='dashboard_frequency').values('config_value')[0]['config_value'],
                          'width':Config.objects.filter(config_name='dashboard_width').values('config_value')[0]['config_value'],
                          'height':Config.objects.filter(config_name='dashboard_height').values('config_value')[0]['config_value'],
                          'font':Config.objects.filter(config_name='dashboard_font').values('config_value')[0]['config_value']}]

    # Add any custom graph URLs the user may have added
    # The user must be authenticated
    if request.user.is_authenticated():
        custom_urls = Url_Subscription.objects.filter(user__username=request.user.username).values('url_id__url')
        for url in custom_urls:
            url_list[url['url_id__url']] = 'custom'

    # Determine the refresh rate
    refresh = Config.objects.filter(config_name='dashboard_refresh').values('config_value')[0]['config_value']

    # Print the page
    if not url_list:
        return render_to_response(
         'error/error.html',
          {
            'title':'Error',
            'error':'No urls selected to display'
          },
          context_instance=RequestContext(request)
        )
    else:
        return render_to_response(
           'dashboard/index.html',               
           {
              'title':'Dashboard',
              'url_list':url_list,
              'dash_settings':dash_settings,
     	      'refresh':refresh
           },
           context_instance=RequestContext(request)
    )
