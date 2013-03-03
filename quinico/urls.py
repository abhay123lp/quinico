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


from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # keyword_rank upload area of admin site
    url(r'^admin/keyword_rank/upload$',  'quinico.keyword_rank.views.upload'),

    # Data job manager area of admin site
    url(r'^admin/datajobs$',  'quinico.main.views.datajobs'),

    # Configuration area of admin site
    url(r'^admin/config$',  'quinico.main.views.config'),

    # User login
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),

    # User logout
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',{'next_page': '/'}),

    # Standard Django admin
    url(r'^admin/', include(admin.site.urls)),

    # Quinico specific URLs
    url(r'^$',                       'quinico.main.views.index'),
    url(r'^keyword_rank/dashboard$', 'quinico.keyword_rank.views.dashboard'),
    url(r'^keyword_rank/trends$',    'quinico.keyword_rank.views.trends'),
    url(r'^seomoz/dashboard$',       'quinico.seomoz.views.dashboard'),
    url(r'^seomoz/trends$',          'quinico.seomoz.views.trends'),
    url(r'^pagespeed/breakdown$',    'quinico.pagespeed.views.breakdown'),
    url(r'^pagespeed/report$',       'quinico.pagespeed.views.report'),
    url(r'^pagespeed/trends$',       'quinico.pagespeed.views.trends'),
    url(r'^pagespeed/history$',      'quinico.pagespeed.views.history'),
    url(r'^webpagetest/history$',    'quinico.webpagetest.views.history'),
    url(r'^webpagetest/report$',     'quinico.webpagetest.views.report'),
    url(r'^webpagetest/trends$',     'quinico.webpagetest.views.trends'),
    url(r'^dashboard/$',             'quinico.dashboard.views.index'),
    url(r'^dashboard/admin$',        'quinico.dashboard.views.admin'),
    url(r'^webmaster/queries$',      'quinico.webmaster.views.queries'),
    url(r'^webmaster/summary$',      'quinico.webmaster.views.summary'),
    url(r'^webmaster/trends$',       'quinico.webmaster.views.trends'),
    url(r'^webmaster/total$',        'quinico.webmaster.views.total'),
    url(r'^status/api$',             'quinico.status.views.api')
)
