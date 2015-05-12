# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns
from rest_framework.urlpatterns import format_suffix_patterns
from .views import DatasetList, DatasetDetail


urlpatterns = patterns('',
                       url(r'datasets$', DatasetList.as_view(), name='dataset-list'),
                       url(r'datasets/(?P<pk>[0-9]+)/$', DatasetDetail.as_view(), name='dataset-detail'),
                       )

urlpatterns = format_suffix_patterns(urlpatterns)
