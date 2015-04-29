# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from urlparse import urlparse

from django.db import migrations
from django.conf import settings

import os
from pyaxiom.netcdf import EnhancedDataset, EnhancedMFDataset


def path(dataset):
    if urlparse(dataset.uri).scheme == "" and not dataset.uri.startswith("/"):
        # We have a relative path, make it absolute to the sciwms directory.
        return str(os.path.realpath(os.path.join(settings.PROJECT_ROOT, dataset.uri)))
    else:
        return str(dataset.uri)


def netcdf4_dataset(dataset):
    try:
        return EnhancedDataset(path(dataset))
    except:
        try:
            return EnhancedMFDataset(path(dataset), aggdim='time')
        except:
            return None


def process_layers(Style, Layer, dataset):
    nc = netcdf4_dataset(dataset)
    if nc is not None:
        for v in nc.variables:
            l, _ = Layer.objects.get_or_create(dataset_id=dataset.id, var_name=v)

            nc_var = nc.variables[v]
            if hasattr(nc_var, 'valid_range'):
                l.default_min = nc_var.valid_range[0]
                l.default_max = nc_var.valid_range[-1]
            # valid_min and valid_max take presendence
            if hasattr(nc_var, 'valid_min'):
                l.default_min = nc_var.valid_min
            if hasattr(nc_var, 'valid_max'):
                l.default_max = nc_var.valid_max

            if hasattr(nc_var, 'standard_name'):
                std_name = nc_var.standard_name
                l.std_name = std_name

                # Set some standard styles
                l.styles = Style.objects.filter(colormap='jet', image_type__in=['filledcontours', 'contours', 'facets', 'pcolor'])
                l.save()

            l.save()

        nc.close()


def forward(apps, schema_editor):
    Dataset = apps.get_model('wms', 'Dataset')
    Layer = apps.get_model('wms', 'Layer')
    Style = apps.get_model('wms', 'Style')

    for d in Dataset.objects.all():
        process_layers(Style, Layer, d)

    try:
        d = Dataset.objects.get(name='UGridTest')
        for l in d.layer_set.all():
            if l.var_name not in ['z', 'surface_temp', 'surface_salt', 'std_temp', 'std_salt', 'elev']:
                l.delete()
    except Dataset.DoesNotExist:
        pass

    try:
        d = Dataset.objects.get(name='SGridTest')
        for l in d.layer_set.all():
            if l.var_name not in ['u', 'v']:
                l.delete()
    except Dataset.DoesNotExist:
        pass


def reverse(apps, schema_editor):
    Layer = apps.get_model('wms', 'Layer')
    Layer.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0016_layer_std_name'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=reverse),
    ]
