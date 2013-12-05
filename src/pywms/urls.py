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

from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^do/', 'wms.views.fvDo'),
    url(r'^doc', 'wms.views.documentation'),
    url(r'^wms/(?P<dataset>.*)/', 'wms.views.wms'),

    url(r'^wmstest/openlayers/(?P<filepath>.*)', 'wms.views.openlayers'),
    url(r'^wmstest/', 'wms.views.wmstest'),
    url(r'^wmstest', 'wms.views.wmstest'),
    url(r'^leaflet/', 'wms.views.leaflet'),
    url(r'^leaflet', 'wms.views.wmstest'),
    url(r'^static/(?P<filepath>.*)', 'wms.views.static'),
    url(r'^crossdomain.xml', 'wms.views.crossdomain'),

    url(r'^datasets', 'wms.views.datasets'),
    url(r'^update', 'wms.views.update'),
    url(r'^add_dataset', 'wms.views.add'),  # This is a POST based view
    url(r'^add_to_group', 'wms.views.add_to_group'),
    url(r'^remove_dataset', 'wms.views.remove'),
    url(r'^remove_from_group', 'wms.views.remove_from_group'),
    #url(r'^testdb', 'wms.views.testdb'),

    url(r'^index', 'wms.views.index'),
    url(r'^$', 'wms.views.index'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/doc', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin', include(admin.site.urls)),

    url(r'^(?P<group>.*)/wmstest/$', 'wms.views.grouptest'),
    url(r'^(?P<group>.*)/wmstest', 'wms.views.grouptest'),
    url(r'^(?P<group>.*)/', 'wms.views.groups'),
    url(r'^(?P<group>.*)', 'wms.views.groups'),
    )
