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

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns( '',
                        url(r'^grappelli/', include('grappelli.urls')),
                        url(r'^admin/', include(admin.site.urls), name='admin'),

                        url(r'^$', 'wms.views.index', name='index'),

                        url(r'^crossdomain\.xml$', 'wms.views.crossdomain'),
                        url(r'^favicon.ico$', 'wms.views.favicon'),

                        url(r'^wms/', include('wms.urls')),
                        url(r'^rest/', include('wmsrest.urls')),

                        url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout')
                    )

# So we don't have to run "collectstatic" in development mode
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
