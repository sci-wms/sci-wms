# -*- coding: utf-8 -*-
from django.conf.urls import url

from wms.views import (
  DatasetListView,
  DatasetShowView,
  DefaultsView,
  demo,
  groups,
  index,
  LogsView,
  update_dataset,
  WmsView,
)

urlpatterns = [
    url(r'^$', index, name='wms-index'),
    # Datasets
    url(r'^datasets$', DatasetListView.as_view(), name='add_dataset'),
    url(r'^datasets/(?P<dataset>.*)/show', DatasetShowView.as_view(), name="show_dataset"),
    url(r'^datasets/(?P<dataset>.*)/update', update_dataset, name="update_dataset"),
    url(r'^datasets/(?P<dataset>.*)', WmsView.as_view(), name="dataset"),
    # Clients
    url(r'^demo', demo, name='demo'),
    url(r'^defaults$', DefaultsView.as_view(), name='defaults'),
    url(r'^groups/(?P<group>.*)/', groups),
    url(r'^logs$', LogsView.as_view(), name='logs')
]
