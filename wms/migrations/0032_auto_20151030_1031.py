# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0031_auto_20151029_1205'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='default_style',
            field=models.ForeignKey(null=True, related_name='l_default_style', on_delete=django.db.models.deletion.SET_NULL, to='wms.Style'),
        ),
        migrations.AddField(
            model_name='virtuallayer',
            name='default_style',
            field=models.ForeignKey(null=True, related_name='vl_default_style', on_delete=django.db.models.deletion.SET_NULL, to='wms.Style'),
        ),
    ]
