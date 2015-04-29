# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0012_layer_default_max'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='default_min',
            field=models.FloatField(default=None, help_text=b'If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.', null=True, blank=True),
            preserve_default=True,
        ),
    ]
