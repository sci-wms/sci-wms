# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0007_auto_20150424_1604'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='style',
            name='colormap',
        ),
        migrations.RemoveField(
            model_name='style',
            name='layer',
        ),
        migrations.RemoveField(
            model_name='style',
            name='param_loc',
        ),
        migrations.RemoveField(
            model_name='style',
            name='wildcard',
        ),
        migrations.AddField(
            model_name='layer',
            name='styles',
            field=models.ManyToManyField(to='wms.Style'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='style',
            name='description',
            field=models.CharField(help_text=b'Descriptive name of this style, optional', max_length=200, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='style',
            name='image_type',
            field=models.CharField(default=b'filledcontours', max_length=200, choices=[(b'filledcontours', b'filledcontours'), (b'contours', b'contours'), (b'pcolor', b'pcolor'), (b'facets', b'facets'), (b'composite', b'composite'), (b'vectors', b'vectors'), (b'barbs', b'barbs')]),
            preserve_default=True,
        ),
    ]
