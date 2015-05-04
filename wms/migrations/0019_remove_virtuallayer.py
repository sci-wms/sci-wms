# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0018_add_style_to_virtuallayers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='virtuallayer',
            name='datasets',
        ),
        migrations.RemoveField(
            model_name='virtuallayer',
            name='styles',
        ),
        migrations.DeleteModel(
            name='VirtualLayer',
        ),
    ]
