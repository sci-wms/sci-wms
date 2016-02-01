# -*- coding: utf-8 -*-
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from wmsrest.views import DatasetList, DatasetDetail, LayerDetail, VirtuallLayerDetail, DefaultDetail, DefaultList, UnidentifiedDatasetList, UnidentifiedDatasetDetail


urlpatterns = [
    url(r'datasets$', DatasetList.as_view(), name='dataset-list'),
    url(r'datasets/(?P<pk>[0-9]+)/$', DatasetDetail.as_view(), name='dataset-detail'),
    url(r'vlayers/(?P<pk>[0-9]+)/$', VirtuallLayerDetail.as_view(), name='vlayer-detail'),
    url(r'layers/(?P<pk>[0-9]+)/$', LayerDetail.as_view(), name='layer-detail'),
    url(r'defaults$', DefaultList.as_view(), name='default-list'),
    url(r'defaults/(?P<pk>[0-9]+)/$', DefaultDetail.as_view(), name='default-detail'),
    url(r'new$', UnidentifiedDatasetList.as_view(), name='add-dataset'),
    url(r'unid$', UnidentifiedDatasetList.as_view(), name='unid-list'),
    url(r'unid/(?P<pk>[0-9]+)/$', UnidentifiedDatasetDetail.as_view(), name='unid-detail'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
