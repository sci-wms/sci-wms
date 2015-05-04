# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0024_auto_20150501_1731'),
    ]

    operations = [
        migrations.CreateModel(
            name='RGridDataset',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('wms.dataset',),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='type',
            field=models.CharField(db_index=True, max_length=255, choices=[('wms.ugriddataset', 'u grid dataset'), ('wms.sgriddataset', 's grid dataset'), ('wms.rgriddataset', 'r grid dataset')]),
            preserve_default=True,
        ),
    ]
