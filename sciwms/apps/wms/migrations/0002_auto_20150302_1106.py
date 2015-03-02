# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='keep_up_to_date',
            field=models.BooleanField(default=True, help_text=b'Check this box to keep the dataset up-to-date if changes are made to it on disk or remote server.'),
            preserve_default=True,
        ),
    ]
