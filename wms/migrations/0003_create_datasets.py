# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.db import migrations


def create_styles(apps, schema_editor):
    resource_path = os.path.join(settings.BASE_DIR, 'wms', 'resources')

    Dataset = apps.get_model('wms', 'Dataset')

    sgrid, created = Dataset.objects.get_or_create(name="SGridTest")
    sgrid.type = 'wms.sgriddataset'
    sgrid.uri = os.path.join(resource_path, "coawst_sgrid.nc")
    sgrid.title = "SGrid Test dataset"
    sgrid.abstract = "SGrid Test data set for sci-wms"
    sgrid.display_all_timesteps = False
    sgrid.keep_up_to_date = False
    sgrid.save()

    ugrid, created = Dataset.objects.get_or_create(name="UGridTest")
    ugrid.type = 'wms.ugriddataset'
    ugrid.uri = os.path.join(resource_path, "selfe_ugrid.nc")
    ugrid.title = "UGrid Test dataset"
    ugrid.abstract = "UGrid Test data set for sci-wms"
    ugrid.display_all_timesteps = False
    ugrid.keep_up_to_date = False
    ugrid.save()


def remove_styles(apps, schema_editor):
    Dataset = apps.get_model('wms', 'Dataset')
    Dataset.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0002_create_styles'),
    ]

    operations = [
        migrations.RunPython(create_styles, reverse_code=remove_styles),
    ]
