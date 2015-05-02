# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0023_auto_20150501_1427'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatasetOriginal',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('wms.dataset',),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='name',
            field=models.CharField(help_text=b"Name/ID to use. No special characters or spaces ('_','0123456789' and A-Z are allowed).", unique=True, max_length=200),
            preserve_default=True,
        ),
    ]
