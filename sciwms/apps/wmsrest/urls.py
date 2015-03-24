'''
Created on Feb 12, 2015

@author: ayan
'''
from django.conf.urls import url, patterns
from rest_framework.urlpatterns import format_suffix_patterns
from .views import DatasetList, VirtualLayerList, DatasetDetail, VirtualLayerDetail


urlpatterns = patterns('',
                       url(r'datasets/$', DatasetList.as_view(), name='dataset-list'),
                       url(r'datasets/(?P<pk>[0-9]+)/$', DatasetDetail.as_view(), name='dataset-detail'),
                       url(r'virtuallayers/$', VirtualLayerList.as_view(), name='virtuallayers-list'),
                       url(r'virtuallayers/(?P<pk>[0-9]+)/$', VirtualLayerDetail.as_view(), name='virtuallayers-detail'),
                       )


urlpatterns = format_suffix_patterns(urlpatterns)