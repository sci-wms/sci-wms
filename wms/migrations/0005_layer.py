# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0004_auto_20150310_0955'),
    ]

    operations = [
        migrations.CreateModel(
            name='Layer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('var_name', models.CharField(help_text=b'Variable name from dataset', max_length=200)),
                ('description', models.CharField(help_text=b'Descriptive name of this layer, optional', max_length=200, blank=True)),
                ('style', models.CharField(help_text=b'WMS style string', max_length=200)),
                ('dataset', models.ForeignKey(to='wms.Dataset')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
