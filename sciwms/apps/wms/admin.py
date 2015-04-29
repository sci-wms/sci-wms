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

Created on Sep 6, 2011

@author: ACrosby
'''
from django.contrib import admin
from sciwms.apps.wms.models import Dataset, Server, Group, VirtualLayer, Layer, Style


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('title', 'keywords', 'contact_person', 'contact_email')


class VirtualLayerInline(admin.StackedInline):
    model = VirtualLayer.datasets.through
    extra = 1


class GroupInline(admin.TabularInline):
    model = Group.datasets.through
    extra = 1


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'abstract')
    inlines = [
        GroupInline,
    ]


class LayerInline(admin.StackedInline):
    model = Layer
    extra = 0
    filter_horizontal = ('styles',)


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'keep_up_to_date')
    list_filter = ('keep_up_to_date',)
    inlines = [
        LayerInline,
        VirtualLayerInline,
        GroupInline,
    ]


@admin.register(VirtualLayer)
class VirtualLayerAdmin(admin.ModelAdmin):
    list_display = ('layer', 'layer_expression')
    filter_horizontal = ('styles',)
    inlines = [
        VirtualLayerInline,
    ]
