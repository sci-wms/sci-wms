# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, utils


def create_styles(apps, schema_editor):
    Style = apps.get_model('wms', 'Style')

    for it, _ in Style._meta.get_field('image_type').choices:
        for cmap, _ in Style._meta.get_field('colormap').choices:
            try:
                Style.objects.create(colormap=cmap, image_type=it)
            except utils.IntegrityError:
                pass


def remove_styles(apps, schema_editor):
    Style = apps.get_model('wms', 'Style')

    for it, _ in Style._meta.get_field('image_type').choices:
        for cmap, _ in Style._meta.get_field('colormap').choices:
            try:
                Style.objects.get(colormap=cmap, image_type=it).delete()
            except Style.DoesNotExist:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0009_auto_20150428_2030'),
    ]

    operations = [
        migrations.RunPython(create_styles, reverse_code=remove_styles),
    ]
