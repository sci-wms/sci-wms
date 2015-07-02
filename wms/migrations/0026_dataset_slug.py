# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import string

from django.db import models, migrations

import autoslug.fields


def random_string():
    char_set = string.ascii_uppercase + string.digits
    return ''.join(random.sample(char_set*6, 6))


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0025_auto_20150504_1143'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from='name', default=random_string),
            preserve_default=False,
        ),
    ]
