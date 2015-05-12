# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0010_auto_20150428_2201'),
    ]

    operations = [
        migrations.AddField(
            model_name='virtuallayer',
            name='styles',
            field=models.ManyToManyField(to='wms.Style'),
            preserve_default=True,
        ),
    ]
