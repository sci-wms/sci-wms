# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0019_remove_virtuallayer'),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualLayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('var_name', models.CharField(help_text=b'Variable name from dataset', max_length=200)),
                ('std_name', models.CharField(help_text=b"The 'standard_name' from the dataset variable", max_length=200, blank=True)),
                ('description', models.CharField(help_text=b'Descriptive name of this layer, optional', max_length=200, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('default_min', models.FloatField(default=None, help_text=b'If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.', null=True, blank=True)),
                ('default_max', models.FloatField(default=None, help_text=b'If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.', null=True, blank=True)),
                ('dataset', models.ForeignKey(to='wms.Dataset')),
                ('styles', models.ManyToManyField(to='wms.Style')),
            ],
            options={
                'ordering': ('var_name',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='layer',
            options={'ordering': ('var_name',)},
        ),
    ]
