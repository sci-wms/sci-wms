# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0028_auto_20150710_1637'),
    ]

    operations = [
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('std_name', models.CharField(help_text=b"The 'standard_name' of this variable", max_length=200)),
                ('units', models.CharField(help_text=b"The 'units' of this variable", max_length=200, blank=True)),
                ('logscale', models.BooleanField(default=False, help_text=b'If this variable should default to a log scale')),
                ('default_min', models.FloatField(default=None, help_text=b'If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.', null=True, blank=True)),
                ('default_max', models.FloatField(default=None, help_text=b'If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.', null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='variable',
            unique_together=set([('std_name', 'units')]),
        ),
        migrations.AddField(
            model_name='layer',
            name='logscale',
            field=models.NullBooleanField(default=None, help_text=b'If this dataset variable should default to a log scale'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='virtuallayer',
            name='logscale',
            field=models.NullBooleanField(default=None, help_text=b'If this dataset variable should default to a log scale'),
            preserve_default=True,
        ),
    ]
