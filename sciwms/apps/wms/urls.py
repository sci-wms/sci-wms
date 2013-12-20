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
from django.conf import settings

urlpatterns = patterns( '',

                        url(r'^index', 'sciwms.apps.wms.views.index'),
                        url(r'^$', 'sciwms.apps.wms.views.index'),

                        url(r'^documentation/', 'sciwms.apps.wms.views.documentation', name='documentation'),

                        # Datasets
                        url(r'^datasets$',  'sciwms.apps.wms.views.datasets'),
                        url(r'^datasets/$', 'sciwms.apps.wms.views.datasets'),
                        url(r'^datasets/(?P<dataset>.*)/', 'sciwms.apps.wms.views.wms', name="dataset"),

                        # Clients
                        url(r'^openlayers/(?P<filepath>.*)', 'sciwms.apps.wms.views.openlayers'),
                        url(r'^simple', 'sciwms.apps.wms.views.simpleclient', name='simpleclient'),
                        url(r'^leaflet', 'sciwms.apps.wms.views.leafletclient', name='leafletclient'),

                        url(r'^crossdomain.xml', 'sciwms.apps.wms.views.crossdomain'),

                        url(r'^update', 'sciwms.apps.wms.views.update'),
                        url(r'^add_dataset', 'sciwms.apps.wms.views.add'),  # This is a POST based view
                        url(r'^add_to_group', 'sciwms.apps.wms.views.add_to_group'),
                        url(r'^remove_dataset', 'sciwms.apps.wms.views.remove'),
                        url(r'^remove_from_group', 'sciwms.apps.wms.views.remove_from_group'),

                        url(r'^groups/(?P<group>.*)/wmstest/$', 'sciwms.apps.wms.views.grouptest'),
                        url(r'^groups/(?P<group>.*)/wmstest', 'sciwms.apps.wms.views.grouptest'),
                        url(r'^groups/(?P<group>.*)/', 'sciwms.apps.wms.views.groups'),
                        url(r'^groups/(?P<group>.*)', 'sciwms.apps.wms.views.groups')
                    )
