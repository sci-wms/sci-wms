# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0013_layer_default_min'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataset',
            name='latitude_variable',
        ),
        migrations.RemoveField(
            model_name='dataset',
            name='longitude_variable',
        ),
        migrations.RemoveField(
            model_name='dataset',
            name='test_layer',
        ),
        migrations.RemoveField(
            model_name='dataset',
            name='test_style',
        ),
    ]
