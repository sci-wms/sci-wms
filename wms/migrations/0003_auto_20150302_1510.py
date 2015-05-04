# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.conf import settings
from django.db import migrations


def forwards(apps, schema_editor):
    resource_path = os.path.join(settings.PROJECT_ROOT, '..', 'wms', 'resources')

    Dataset = apps.get_model("wms", "Dataset")
    d1 = Dataset(uri                   = os.path.join(resource_path, "nasa_scb20111015.nc"),
                 name                  = "CGridTest",
                 title                 = "CGrid Test dataset",
                 abstract              = "CGrid Test data set for sci-wms",
                 display_all_timesteps = False,
                 keep_up_to_date       = False,
                 test_layer            = "u,v",
                 test_style            = "facets_average_jet_None_None_grid_False" )
    d1.save()

    d2 = Dataset(uri                   = os.path.join(resource_path, "201220109.nc"),
                 name                  = "UGridTest",
                 title                 = "UGrid Test dataset",
                 abstract              = "UGrid Test data set for sci-wms",
                 display_all_timesteps = False,
                 keep_up_to_date       = False,
                 test_layer            = "u,v",
                 test_style            = "facets_average_jet_None_None_node_False" )
    d2.save()

    VirtualLayer = apps.get_model('wms', 'VirtualLayer')
    uv = VirtualLayer(layer="U,V vectors", layer_expression="u,v")
    uv.save()
    uv.datasets.add(d1)
    uv.datasets.add(d2)
    uv.save()

    bands = VirtualLayer(layer="RGB Band Images", layer_expression="Band1*Band2*Band3")
    bands.save()


def backwards(apps, schema_editor):
    Dataset = apps.get_model("wms", "Dataset")
    Dataset.objects.filter(name='CGridTest').all().delete()
    Dataset.objects.filter(name='UGridTest').all().delete()

    VirtualLayer = apps.get_model('wms', 'VirtualLayer')
    VirtualLayer.objects.filter(layer_expression='u,v').all().delete()
    VirtualLayer.objects.filter(layer_expression="Band1*Band2*Band3").all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0002_auto_20150302_1106'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=backwards),
    ]
