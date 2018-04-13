# -*- coding: utf-8 -*-
from django.conf.urls import url

from wms.views import (
    DatasetDeleteCacheView,
    DatasetGridUpdateView,
    DatasetLayersUpdateView,
    DatasetShowView,
    DatasetTimeUpdateView,
    DatasetUpdateView,
    DefaultsView,
    demo,
    groups,
    index,
    LogsView,
    WmsView,
)

urlpatterns = [
    url(r'^$', index, name='wms-index'),
    # Datasets
    url(r'^datasets/(?P<dataset>.*)/show', DatasetShowView.as_view(), name="show_dataset"),
    url(r'^datasets/(?P<dataset>.*)/update$', DatasetUpdateView.as_view(), name="update_dataset"),
    url(r'^datasets/(?P<dataset>.*)/update_time$', DatasetTimeUpdateView.as_view(), name="update_time"),
    url(r'^datasets/(?P<dataset>.*)/update_grid$', DatasetGridUpdateView.as_view(), name="update_grid"),
    url(r'^datasets/(?P<dataset>.*)/update_layers$', DatasetLayersUpdateView.as_view(), name="update_layers"),
    url(r'^datasets/(?P<dataset>.*)/delete_cache$', DatasetDeleteCacheView.as_view(), name="delete_cache"),
    url(r'^datasets/(?P<dataset>.*)', WmsView.as_view(), name="dataset"),
    # Clients
    url(r'^demo', demo, name='demo'),
    url(r'^defaults$', DefaultsView.as_view(), name='defaults'),
    url(r'^groups/(?P<group>.*)/', groups),
    url(r'^logs$', LogsView.as_view(), name='logs')
]
