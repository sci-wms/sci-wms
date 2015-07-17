# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0029_auto_20150716_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variable',
            name='logscale',
            field=models.NullBooleanField(default=None, help_text=b'If this variable should default to a log scale'),
            preserve_default=True,
        ),
    ]
