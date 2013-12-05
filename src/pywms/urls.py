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

    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/doc', include('django.contrib.admindocs.urls')),

    url(r'^doc', 'pywms.wms.views.documentation'),
    url(r'^wms/(?P<dataset>.*)/', 'pywms.wms.views.wms'),

    url(r'^wmstest/openlayers/(?P<filepath>.*)', 'pywms.wms.views.openlayers'),
    url(r'^wmstest/', 'pywms.wms.views.wmstest'),
    url(r'^wmstest', 'pywms.wms.views.wmstest'),
    url(r'^leaflet/', 'pywms.wms.views.leaflet'),
    url(r'^leaflet', 'pywms.wms.views.wmstest'),
    url(r'^static/(?P<filepath>.*)', 'pywms.wms.views.static'),
    url(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/favicon.ico'}),
    url(r'^crossdomain.xml', 'pywms.wms.views.crossdomain'),

    url(r'^datasets', 'pywms.wms.views.datasets'),
    url(r'^update', 'pywms.wms.views.update'),
    url(r'^add_dataset', 'pywms.wms.views.add'),  # This is a POST based view
    url(r'^add_to_group', 'pywms.wms.views.add_to_group'),
    url(r'^remove_dataset', 'pywms.wms.views.remove'),
    url(r'^remove_from_group', 'pywms.wms.views.remove_from_group'),
    #url(r'^testdb', 'pywms.wms.views.testdb'),

    url(r'^index', 'pywms.wms.views.index'),
    url(r'^$', 'pywms.wms.views.index'),

    url(r'^(?P<group>.*)/wmstest/$', 'pywms.wms.views.grouptest'),
    url(r'^(?P<group>.*)/wmstest', 'pywms.wms.views.grouptest'),
    url(r'^(?P<group>.*)/', 'pywms.wms.views.groups'),
    url(r'^(?P<group>.*)', 'pywms.wms.views.groups'),
    )
