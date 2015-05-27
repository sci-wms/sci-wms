# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns
from rest_framework.urlpatterns import format_suffix_patterns
from .views import DatasetList, DatasetDetail, LayerDetail, VirtuallLayerDetail


urlpatterns = patterns('',
                       url(r'datasets$', DatasetList.as_view(), name='dataset-list'),
                       url(r'datasets/(?P<pk>[0-9]+)/$', DatasetDetail.as_view(), name='dataset-detail'),
                       url(r'vlayers/(?P<pk>[0-9]+)/$', VirtuallLayerDetail.as_view(), name='vlayer-detail'),
                       url(r'layers/(?P<pk>[0-9]+)/$', LayerDetail.as_view(), name='layer-detail'),
                       )

urlpatterns = format_suffix_patterns(urlpatterns)
