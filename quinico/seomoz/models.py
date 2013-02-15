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


"""Models for the Quinico SEOMoz Application

   Any models that will be displayed in the DJango admin will have unicode
   methods to display them properly in the admin

"""


from django.db import models


class Url(models.Model):
    """URLs that will be tested"""

    url = models.CharField(max_length=200, unique=True)

    # Represent the object as unicode
    def __unicode__(self):
        return self.url


class Update(models.Model):
    """Data Updates (when data has been updated from SEOMoz)"""

    date = models.DateTimeField(null=False,blank=False)


class Competitor(models.Model):
    """Competitors"""

    url = models.ForeignKey(Url,related_name='primary')
    comp = models.ForeignKey(Url,related_name='competitor')

    class Meta:
        unique_together = ['url','comp']


class API_Calls(models.Model):
    """Count of SEOMoz API calls"""

    call_date = models.DateField(null=False,blank=False,unique=True)
    count = models.IntegerField(max_length=11)


class API_Errors(models.Model):
    """Count of SEOMoz API errors"""

    call_date = models.DateField(null=False,blank=False,unique=True)
    count = models.IntegerField(max_length=11)


class Metrics(models.Model):
    """SEO Metrics"""

    date = models.DateField(null=False,blank=False)
    url = models.ForeignKey(Url)
    ueid =  models.IntegerField(max_length=20)  	         
    feid =  models.IntegerField(max_length=20)                   
    peid =  models.IntegerField(max_length=20)                   
    ujid =  models.IntegerField(max_length=20)                   
    uifq =  models.IntegerField(max_length=20)                   
    uipl =  models.IntegerField(max_length=20)                   
    uid =  models.IntegerField(max_length=20)                    
    fid =  models.IntegerField(max_length=20)                    
    pid =  models.IntegerField(max_length=20)                    
    umrp =  models.DecimalField(decimal_places=1,max_digits=20)  
    fmrp =  models.DecimalField(decimal_places=1,max_digits=20)  
    pmrp =  models.DecimalField(decimal_places=1,max_digits=20)  
    utrp =  models.DecimalField(decimal_places=1,max_digits=20)  
    ftrp =  models.DecimalField(decimal_places=1,max_digits=20)  
    ptrp =  models.DecimalField(decimal_places=1,max_digits=20)  
    uemrp =  models.DecimalField(decimal_places=1,max_digits=20) 
    fejp =  models.DecimalField(decimal_places=1,max_digits=20)  
    pejp =  models.DecimalField(decimal_places=1,max_digits=20)  
    fjp =  models.DecimalField(decimal_places=1,max_digits=20)   
    pjp =  models.DecimalField(decimal_places=1,max_digits=20)   
    fuid =  models.IntegerField(max_length=20)                   
    puid =  models.IntegerField(max_length=20)                   
    fipl =  models.IntegerField(max_length=20)                   
    upa =  models.IntegerField(max_length=20)                    
    pda =  models.IntegerField(max_length=20)                    


class Description(models.Model):
    """Descriptions for the different metrics"""

    metric = models.CharField(max_length=10, unique=True)
    column_description = models.CharField(max_length=50)
    full_description = models.CharField(max_length=200)
    represent = models.CharField(max_length=7)

