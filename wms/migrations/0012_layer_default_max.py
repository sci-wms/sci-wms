# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0011_auto_20150428_2211'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='default_max',
            field=models.FloatField(default=None, help_text=b'If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.', null=True, blank=True),
            preserve_default=True,
        ),
    ]
