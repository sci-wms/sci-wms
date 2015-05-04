# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards(apps, schema_editor):

    Server = apps.get_model('wms', 'Server')
    server_data = Server(title='Sci-wms Server')
    server_data.save()


def backwards(apps, schema_editor):
    Server = apps.get_model('wms', 'Server')
    Server.objects.filter(title='Sci-wms Server').all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0003_auto_20150302_1510'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=backwards),
    ]
