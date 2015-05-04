# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards(apps, schema_editor):
    Dataset = apps.get_model("wms", "Dataset")
    Dataset.objects.filter(name='UGridTest').update(type='wms.ugriddataset')
    Dataset.objects.filter(name='SGridTest').update(type='wms.sgriddataset')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0022_auto_20150429_1533'),
    ]

    operations = [
        migrations.CreateModel(
            name='SGridDataset',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('wms.dataset',),
        ),
        migrations.CreateModel(
            name='UGridDataset',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('wms.dataset',),
        ),
        migrations.AddField(
            model_name='dataset',
            name='type',
            field=models.CharField(default='wms.ugriddataset', max_length=255, db_index=True, choices=[('wms.ugriddataset', 'u grid dataset'), ('wms.sgriddataset', 's grid dataset')]),
            preserve_default=False,
        ),
        migrations.RunPython(forwards, reverse_code=backwards),
    ]
