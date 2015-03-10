# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def server_title(apps, schema_editor):
    
    Server = apps.get_model('wms', 'Server')
    server_data = Server(title='Sci-wms Server')
    server_data.save()
    

class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0003_auto_20150302_1510'),
    ]

    operations = [
                  migrations.RunPython(server_title),
    ]
