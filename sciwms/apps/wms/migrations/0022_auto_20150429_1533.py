# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0021_auto_20150429_1429'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='active',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='active',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
