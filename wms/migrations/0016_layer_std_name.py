# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0015_change_testing_datasets'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='std_name',
            field=models.CharField(help_text=b"The 'standard_name' from the dataset variable", max_length=200, blank=True),
            preserve_default=True,
        ),
    ]
