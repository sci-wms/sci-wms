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

urlpatterns = patterns( '',

                        url(r'^index', 'sciwms.apps.wms.views.index'),
                        url(r'^$', 'sciwms.apps.wms.views.index'),

                        # Datasets
                        url(r'^datasets/$', 'sciwms.apps.wms.views.datasets'),
                        url(r'^datasets/(?P<dataset>.*)/update', 'sciwms.apps.wms.views.update_dataset', name="update_dataset"),
                        url(r'^datasets/(?P<dataset>.*)/', 'sciwms.apps.wms.views.wms', name="dataset"),

                        # Clients
                        url(r'^demo', 'sciwms.apps.wms.views.demo', name='demo'),

                        url(r'^groups/(?P<group>.*)/', 'sciwms.apps.wms.views.groups'),
                    )
