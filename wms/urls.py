'''
COPYRIGHT 2010 RPS ASA

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.
'''

from django.conf.urls import patterns, url
from wms.views import DatasetListView, WmsView

urlpatterns = patterns('',
                       url(r'^$', 'wms.views.index', name='wms-index'),
                       # Datasets
                       url(r'^datasets$', DatasetListView.as_view(), name='add_dataset'),
                       url(r'^datasets/(?P<dataset>.*)/update', 'wms.views.update_dataset', name="update_dataset"),
                       url(r'^datasets/(?P<dataset>.*)', WmsView.as_view(), name="dataset"),
                       # Clients
                       url(r'^demo', 'wms.views.demo', name='demo'),
                       url(r'^groups/(?P<group>.*)/', 'wms.views.groups')
                    )
