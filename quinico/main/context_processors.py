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


"""Context processor for Quinico

   This context processor is responsible for setting certain universal
   features of Quinico:

     - Version number
     - Help screens

"""
   

from django.conf import settings
from quinico.main.models import Config
from quinico.main.models import Help


def help(request):
    """Set the help screens"""

    help_blurb = None

    try:
        help_blurb = Help.objects.filter(help_name=request.META['PATH_INFO']).values('help_value')[0]['help_value']
    except Exception:
        pass

    return{'help_blurb':help_blurb}


def version(request):
    """Set the version number"""

    return{'app_version':settings.APP_VERSION}


def redirect(request):
    """Set the 'next' Key so that after login events, the user can be 
    sent back to where they were"""

    # If the @login_required decorator is being used on a view,
    # then 'next' will already be set so do nothing
    # Since context_processors must return a dictionary, just give back
    # what is already in 'next'
    if request.GET.has_key('next'):
        return{'next':request.GET['next']}

    # If someone is accessing the login link directly, then set the next
    # key to the referring page so they can be redirected to the page they 
    # were on after login
    elif 'HTTP_REFERER' in request.META:

        # If the referring page is 'http://<quinico server>/accounts/login', then its probably
        # a failed login, so send them back to the homepage after login
        # since we don't know the true referrer
        if request.META['HTTP_REFERER'] == 'http://%s/accounts/login/' % request.META['HTTP_HOST']:
            return{'next':'/'}
        else:
            return{'next':request.META['HTTP_REFERER']}

    # Its not an @login_required view and there is no referrer, so send
    # them back to the home page after login
    else:
        return{'next':'/'}

