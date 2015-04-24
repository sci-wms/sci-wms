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
#from fvcom_compute.wms.models import Node, Cell, Time, Level
#import fvcom_compute.wms.grid_init_script as gridinit
from django.contrib import admin
#from django.db import models
from nested_inline.admin import NestedTabularInline, NestedModelAdmin, NestedStackedInline
from sciwms.apps.wms.models import Dataset, Server, Group, VirtualLayer, Layer, Style


class ServerAdmin(admin.ModelAdmin):
    list_display = ('title', 'keywords', 'contact_person', 'contact_email')


class VirtualLayerInline(admin.StackedInline):
    extra = 0
    model = VirtualLayer.datasets.through


class GroupInline(admin.StackedInline):
    extra = 0
    model = Group.datasets.through


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'abstract')
    inlines = [
        GroupInline,
    ]

class StyleInline(NestedTabularInline):
    ordering = ('style', 'description')
    model = Style
    extra = 1
    fk_name = 'layer'

class LayerInline(NestedStackedInline):
    model = Layer
    extra = 1
    fk_name = 'dataset'
    inlines = [
        StyleInline
    ]


class DatasetAdmin(NestedModelAdmin):
    model = Dataset
    list_display = ('name', 'title', 'keep_up_to_date')
    list_filter = ('keep_up_to_date',)
    inlines = [
        LayerInline,
        VirtualLayerInline,
        GroupInline,
    ]


class VirtualLayerAdmin(admin.ModelAdmin):
    list_display = ('layer', 'layer_expression')
    inlines = [
        VirtualLayerInline,
    ]

#class LayerAdmin(admin.ModelAdmin):
#    list_display = ('var_name', 'active', 'description')


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(VirtualLayer, VirtualLayerAdmin)
#admin.site.register(Layer, LayerAdmin) 
