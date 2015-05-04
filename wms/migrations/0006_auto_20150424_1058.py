# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0005_layer'),
    ]

    operations = [
        migrations.CreateModel(
            name='Style',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(help_text=b'Descriptive name of this layer, optional', max_length=200, blank=True)),
                ('style', models.CharField(help_text=b'WMS style string', max_length=200)),
                ('layer', models.ForeignKey(to='wms.Layer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='layer',
            name='style',
        ),
        migrations.AddField(
            model_name='layer',
            name='active',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
