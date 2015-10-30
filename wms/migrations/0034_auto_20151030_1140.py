# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, utils
import wms.models.layer

from wms import logger


def forward(apps, schema_editor):
    Style = apps.get_model('wms', 'Style')
    VirtualLayer = apps.get_model('wms', 'VirtualLayer')
    Layer = apps.get_model('wms', 'Layer')
    SGridDataset = apps.get_model('wms', 'SGridDataset')
    UGridDataset = apps.get_model('wms', 'UGridDataset')

    default_layer_style = wms.models.layer.get_default_layer_style()
    default_vlayer_style = wms.models.layer.get_default_vlayer_style()

    # Add styles
    pks = [default_layer_style, default_vlayer_style]
    for it, _ in Style._meta.get_field('image_type').choices:
        for cmap, _ in Style._meta.get_field('colormap').choices:
            try:
                s, _ = Style.objects.get_or_create(colormap=cmap, image_type=it)
                pks.append(s.pk)
            except utils.IntegrityError:
                pass

    # Remove orphaned styles
    Style.objects.exclude(pk__in=pks).delete()

    for vl in VirtualLayer.objects.all():
        vl.styles = Style.objects.filter(image_type='vectors', colormap='cubehelix')
        vl.default_style_id = default_vlayer_style
        vl.save()

    for s in SGridDataset.objects.all():
        for l in s.layer_set.all():
            l.styles = Style.objects.filter(image_type__in=['filledcontours', 'contours', 'pcolor', 'filledhatches', 'hatches'], colormap='cubehelix')
            l.default_style_id = default_layer_style
            l.save()

    for u in UGridDataset.objects.all():
        for l in u.layer_set.all():
            l.styles = Style.objects.filter(image_type__in=['filledcontours', 'contours', 'filledhatches', 'hatches'], colormap='cubehelix')
            l.default_style_id = default_layer_style
            l.save()


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0033_auto_20151030_1103'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=reverse),
    ]
