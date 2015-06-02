# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.text import slugify
from django.db import migrations


def forward(apps, schema_editor):
    Dataset = apps.get_model('wms', 'Dataset')
    for d in Dataset.objects.all():
        d.slug = slugify(d.name)
        d.save()


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0026_dataset_slug'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=forward),  # Yes, both forward! This is correct. Don't think about it.
    ]
