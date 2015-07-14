# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from pyaxiom.netcdf import EnhancedDataset, EnhancedMFDataset


def forward(apps, schema_editor):
    Layer = apps.get_model('wms', 'Layer')
    Dataset = apps.get_model('wms', 'Dataset')
    for d in Dataset.objects.all():
        try:
            nc = EnhancedDataset(d.uri)
        except:
            try:
                nc = EnhancedMFDataset(d.uri, aggdim='time')
            except:
                pass

        for v in nc.variables:
            nc_var = nc.variables[v]
            l, _ = Layer.objects.get_or_create(dataset_id=d.id, var_name=v)
            if hasattr(nc_var, 'units'):
                l.units = nc_var.units
                l.save()


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0027_auto_20150602_1603'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='units',
            field=models.CharField(help_text=b"The 'units' from the dataset variable", max_length=200, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='virtuallayer',
            name='units',
            field=models.CharField(help_text=b"The 'units' from the dataset variable", max_length=200, blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(forward, reverse_code=reverse),
    ]
