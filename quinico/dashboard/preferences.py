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


"""Preferences module for the Quinico dashboard application


"""


import urllib
from quinico.keyword_rank.models import Test as Keyword_Test
from quinico.keyword_rank.models import Domain as Keyword_Domain
from quinico.pagespeed.models import Test
from quinico.webpagetest.models import Test as WPT_test
from quinico.seomoz.models import Url
from quinico.webmaster.models import Domain as Webmaster_Domain
from quinico.main.models import Config


class prefs:

    Name = "preferences"

    def __init__(self, logger):
        self.logger = logger


    def keyword_rank(self,url_list,host):
        """Populate keyword graphs"""

        self.logger.debug('Setting up %s default graphs' % 'keyword')

        # Keyword Trend URLs
        # Example: http://www.domain.com/keyword_rank/trends?domain=www.domain.com&keyword=baby%2520names&format=db&gl=com&googlehost=google.com
        keyword_trend_base_url = 'http://%s/keyword_rank/trends?format=db&domain=%s&gl=%s&googlehost=%s&%s'
        keyword_list = Keyword_Test.objects.values('domain__domain','domain__gl','domain__googlehost','keyword__keyword')

        for row in keyword_list:
            # Create the URL
            url = keyword_trend_base_url % (
                                            host,
                                            row['domain__domain'],
                                            row['domain__gl'],
                                            row['domain__googlehost'],
                                            urllib.urlencode({'keyword':row['keyword__keyword'].encode('utf-8')})
                                           )
            url_list[url] = 'graph'

        # Keyword Summary URLs.  There are two types
        # Example 1: http://www.domain.com/keyword_rank/dashboard?domain=www.domain.com&format=db&gl=com&googlehost=google.com  (json)
        # Example 2: http://www.domain.com/keyword_rank/dashboard?domain=www.domain.com&format=db1&gl=com&googlehost=google.com (html)
        # Select all domains that have keywords
        keyword_summary_base_url = 'http://%s/keyword_rank/dashboard?domain=%s&format=db%s&gl=%s&googlehost=%s'
        keyword_domain_list = Keyword_Domain.objects.values('domain','gl','googlehost')
        for row in keyword_domain_list:
            # First the html one
            url_html = keyword_summary_base_url % (host,row['domain'],'',row['gl'],row['googlehost'])
            url_list[url_html] = 'graph'

            # Now the json one
            url_json = keyword_summary_base_url % (host,row['domain'],1,row['gl'],row['googlehost'])
            url_list[url_json] = 'html'

        return url_list


    def pagespeed(self,url_list,host):
        """Populate pagespeed graphs"""

        self.logger.debug('Setting up %s default graphs' % 'pagespeed')

        # Pagespeed Trend and Breakdown Urls
        # Example: 
        # Trend: http://www.domain.com/pagespeed/trends?domain=www.domain.com&url=%252F&strategy=desktop&metric=score&format=db
        # Breakdown: http://www.domain.com/pagespeed/breakdown?domain=www.domain.com&url=%252F&strategy=desktop&format=db
        ps_trend_base_url = 'http://%s/pagespeed/trends?domain=%s&%s&strategy=%s&metric=%s&format=db'
        ps_breakdown_base_url = 'http://%s/pagespeed/breakdown?domain=%s&%s&strategy=%s&format=db2'
        ps_list = Test.objects.values('domain__domain','url__url')

        # The metrics we'll display
        metrics = ['score','numberHosts','numberResources','numberStaticResources','numberCssResources','totalRequestBytes','textResponseBytes','cssResponseBytes','htmlResponseBytes','imageResponseBytes','javascriptResponseBytes','otherResponseBytes']

        # Build the urls for each metric (for mobile and desktop)
        for metric in metrics:
            for url in ps_list:
                # Desktop
                url_json = ps_trend_base_url % (host,
                                                url['domain__domain'],
                                                urllib.urlencode({'url':url['url__url']}),
                                                'desktop',
					        metric)
                url_list[url_json] = 'graph'

                # Mobile
                url_json = ps_trend_base_url % (host,
                                                url['domain__domain'],
                                                urllib.urlencode({'url':url['url__url']}),
                                                'mobile',
                                                metric)
                url_list[url_json] = 'graph'

        # Also add the piechart page breakdown for every URL
        for url in ps_list:
            # Desktop
            url_json = ps_breakdown_base_url % (host,
                                                url['domain__domain'],
                                                urllib.urlencode({'url':url['url__url']}),
                                                'desktop')
            url_list[url_json] = 'pie'

            # Mobile
            url_json = ps_breakdown_base_url % (host,
                                                url['domain__domain'],
                                                urllib.urlencode({'url':url['url__url']}),
                                                'mobile')
            url_list[url_json] = 'pie'

        return url_list


    def webpagetest(self,url_list,host):
        """Populate webpagetest graphs"""

        self.logger.debug('Setting up %s default graphs' % 'webpagetest')

        # Webpagetest Trend Urls
        # Example: http://www.domain.com/webpagetest/trends?test_id=1&metric=score&format=db
        wpt_trend_base_url = 'http://%s/webpagetest/trends?test_id=%s&metric=%s&format=db'
        wpt_trend_list = WPT_test.objects.values('id')

        # The metrics we'll display
        metrics = ['loadTime','bytesOut','bytesOutDoc','bytesIn','bytesInDoc','requests','requestsDoc','render','fullyLoaded','docTime','gzip_total','image_total']

        # Build the urls for each metric
        for metric in metrics:
            for url in wpt_trend_list:
                url_json = wpt_trend_base_url % (host,url['id'],metric)
                url_list[url_json] = 'graph'

        return url_list


    def seomoz(self,url_list,host):
        """Populate seomoz graphs"""

        self.logger.debug('Setting up %s default graphs' % 'seo')

        # Determine if this is a free or paid account
        type = Config.objects.filter(config_name='seomoz_account_type').values('config_value')[0]['config_value']

        # SEO Trend Urls
        # Example: http://www.domain.com/seomoz/trends?url=www.domain.com&metric=ueid&format=db
        seo_trend_base_url = 'http://%s/seomoz/trends?%s&metric=%s&format=db'
        seo_trend_list = Url.objects.values('url')
   
        # If its a free account, there is a reduced set of metrics available
        if type == 'free':
            metrics = ['ueid','uid','umrp','fmrp','upa','pda']
        elif type == 'paid':
            metrics = ['ueid','uid','umrp','fmrp','upa','pda']
        else: 
            # Account type is not set properly, don't set these metrics
            return url_list

        for url in seo_trend_list:
            for metric in metrics:
                url_json = seo_trend_base_url % (host,urllib.urlencode({'url':url['url']}),metric)
                url_list[url_json] = 'graph'

        return url_list


    def webmaster(self,url_list,host):
        """Populate webmaster graphs"""

        self.logger.debug('Setting up %s default graphs' % 'webmaster')

        # Webmaster Total Crawl Error Urls
        # Example: http://www.domain.com/webmaster/total?domain=www.domain.com&format=db
        webmaster_tt_base_url = 'http://%s/webmaster/total?%s&format=db'
        webmaster_tt_list = Webmaster_Domain.objects.values('domain')
        for row in webmaster_tt_list:
            url_json = webmaster_tt_base_url % (host,urllib.urlencode({'domain':row['domain']}))
            url_list[url_json] = 'graph'

        return url_list

