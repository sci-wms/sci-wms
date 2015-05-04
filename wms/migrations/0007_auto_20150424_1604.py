# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0006_auto_20150424_1058'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='style',
            name='style',
        ),
        migrations.AddField(
            model_name='style',
            name='colormap',
            field=models.CharField(default=b'jet', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='style',
            name='image_type',
            field=models.CharField(default=b'filledcontours', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='style',
            name='param_loc',
            field=models.CharField(default=b'grid', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='style',
            name='wildcard',
            field=models.CharField(default=b'False', max_length=200),
            preserve_default=True,
        ),
    ]
