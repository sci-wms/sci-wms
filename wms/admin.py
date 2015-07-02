# -*- coding: utf-8 -*-
from django.contrib import admin
from wms.models import Dataset, Server, Group, VirtualLayer, Layer


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('title', 'keywords', 'contact_person', 'contact_email')


class VirtualLayerInline(admin.StackedInline):
    model = VirtualLayer
    extra = 0
    filter_horizontal = ('styles',)


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

    def has_add_permission(self, request):
        return False


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'title', 'keep_up_to_date')
    list_filter = ('keep_up_to_date',)
    inlines = [
        LayerInline,
        VirtualLayerInline,
        GroupInline,
    ]
