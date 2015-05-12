# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import os
from django.conf import settings


def forward(apps, schema_editor):
    resource_path = os.path.join(settings.PROJECT_ROOT, '..', 'wms', 'resources')

    Dataset = apps.get_model('wms', 'Dataset')

    try:
        Dataset.objects.get(name='CGridTest').delete()
        d1 = Dataset.objects.create(uri                   = os.path.join(resource_path, "coawst_sgrid.nc"),
                                    name                  = "SGridTest",
                                    title                 = "SGrid Test dataset",
                                    abstract              = "SGrid Test data set for sci-wms",
                                    display_all_timesteps = False,
                                    keep_up_to_date       = False)
        d1.save()
    except Dataset.DoesNotExist:
        pass

    try:
        d2 = Dataset.objects.get(name='UGridTest')
        d2.uri = os.path.join(resource_path, "selfe_ugrid.nc")
        d2.save()
    except Dataset.DoesNotExist:
        pass


def reverse(apps, schema_editor):
    resource_path = os.path.join(settings.PROJECT_ROOT, '..', 'wms', 'resources')

    Dataset = apps.get_model('wms', 'Dataset')

    try:
        Dataset.objects.get(name='SGridTest').delete()
        d1 = Dataset.objects.create(uri                   = os.path.join(resource_path, "nasa_scb20111015.nc"),
                                    name                  = "CGridTest",
                                    title                 = "CGrid Test dataset",
                                    abstract              = "CGrid Test data set for sci-wms",
                                    display_all_timesteps = False,
                                    keep_up_to_date       = False)

        d1.save()
    except Dataset.DoesNotExist:
        pass

    try:
        d2 = Dataset.objects.get(name='UGridTest')
        d2.uri = os.path.join(resource_path, "201220109.nc")
        d2.save()
    except Dataset.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0014_auto_20150428_2247'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=reverse),
    ]
