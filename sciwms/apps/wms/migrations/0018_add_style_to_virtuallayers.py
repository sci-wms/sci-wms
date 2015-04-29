# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forward(apps, schema_editor):
    Style = apps.get_model('wms', 'Style')
    VirtualLayer = apps.get_model('wms', 'VirtualLayer')

    try:
        uv = VirtualLayer.objects.get(layer="U,V vectors", layer_expression="u,v")
        uv.styles = Style.objects.filter(image_type__contains='vectors', colormap='jet')
        uv.save()
    except VirtualLayer.DoesNotExist:
        pass

    try:
        bnd = VirtualLayer.objects.get(layer="RGB Band Images", layer_expression="Band1*Band2*Band3")
        sty, _ = Style.objects.get_or_create(image_type='composite', colormap='jet')
        bnd.styles = [sty]
        bnd.save()
    except VirtualLayer.DoesNotExist:
        pass


def reverse(apps, schema_editor):
    VirtualLayer = apps.get_model('wms', 'VirtualLayer')

    try:
        uv = VirtualLayer.objects.get(layer="U,V vectors", layer_expression="u,v")
        uv.styles = []
        uv.save()
    except VirtualLayer.DoesNotExist:
        pass

    try:
        bnd = VirtualLayer.objects.get(layer="RGB Band Images", layer_expression="Band1*Band2*Band3")
        bnd.styles = []
        bnd.save()
    except VirtualLayer.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0017_create_layers'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=reverse),
    ]
