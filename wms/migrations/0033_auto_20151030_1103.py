# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import wms.models.layer


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0032_auto_20151030_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='default_numcontours',
            field=models.IntegerField(default=20),
        ),
        migrations.AddField(
            model_name='virtuallayer',
            name='default_numcontours',
            field=models.IntegerField(default=20),
        ),
        migrations.AlterField(
            model_name='layer',
            name='default_style',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_DEFAULT, related_name='l_default_style', default=wms.models.layer.get_default_layer_style, to='wms.Style'),
        ),
        migrations.AlterField(
            model_name='style',
            name='image_type',
            field=models.CharField(choices=[('filledcontours', 'filledcontours'), ('contours', 'contours'), ('filledhatches', 'filledhatches'), ('hatches', 'hatches'), ('pcolor', 'pcolor'), ('vectors', 'vectors')], max_length=200, default='filledcontours'),
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='default_style',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_DEFAULT, related_name='vl_default_style', default=wms.models.layer.get_default_vlayer_style, to='wms.Style'),
        ),
    ]
