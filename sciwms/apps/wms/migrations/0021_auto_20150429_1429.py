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


def make_vector_layer(apps, us, vs, std_name, style, dataset_id):
    VirtualLayer = apps.get_model('wms', 'VirtualLayer')
    Style = apps.get_model('wms', 'Style')
    for u in us:
        for v in vs:
            if u.standard_name.split('_')[1:] == v.standard_name.split('_')[1:]:
                try:
                    vl = VirtualLayer.objects.create(var_name='{},{}'.format(u._name, v._name),
                                                     std_name=std_name,
                                                     description="U ({}) and V ({}) vectors".format(u._name, v._name),
                                                     dataset_id=dataset_id)
                    vl.styles.add(Style.objects.get(colormap='jet', image_type=style))
                    vl.save()
                    break
                except:
                    raise


def forward(apps, schema_editor):
    Dataset = apps.get_model('wms', 'Dataset')
    VirtualLayer = apps.get_model('wms', 'VirtualLayer')

    # clean slate
    VirtualLayer.objects.all().delete()

    for dataset in Dataset.objects.all():
        nc = netcdf4_dataset(dataset)
        if nc is not None:

            # Earth Projected Sea Water Velocity
            u_names = ['eastward_sea_water_velocity', 'eastward_sea_water_velocity_assuming_no_tide']
            v_names = ['northward_sea_water_velocity', 'northward_sea_water_velocity_assuming_no_tide']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            make_vector_layer(apps, us, vs, 'sea_water_velocity', 'vectors', dataset.id)

            # Grid projected Sea Water Velocity
            u_names = ['x_sea_water_velocity', 'grid_eastward_sea_water_velocity']
            v_names = ['y_sea_water_velocity', 'grid_northward_sea_water_velocity']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            make_vector_layer(apps, us, vs, 'grid_sea_water_velocity', 'vectors', dataset.id)

            # Earth projected Winds
            u_names = ['eastward_wind']
            v_names = ['northward_wind']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            make_vector_layer(apps, us, vs, 'winds', 'barbs', dataset.id)

            # Grid projected Winds
            u_names = ['x_wind', 'grid_eastward_wind']
            v_names = ['northward_wind', 'grid_northward_wind']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            make_vector_layer(apps, us, vs, 'grid_winds', 'barbs', dataset.id)

            # Earth projected Ice velocity
            u_names = ['eastward_sea_ice_velocity']
            v_names = ['northward_sea_ice_velocity']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            make_vector_layer(apps, us, vs, 'sea_ice_velocity', 'vectors', dataset.id)

            nc.close()


def reverse(apps, schema_editor):
    VirtualLayer = apps.get_model('wms', 'VirtualLayer')
    VirtualLayer.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0020_add_back_virtuallayer'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=reverse),
    ]
