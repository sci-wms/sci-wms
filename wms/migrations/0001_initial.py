# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uri', models.CharField(max_length=1000)),
                ('name', models.CharField(help_text=b"Name/ID to use. No special characters or spaces ('_','0123456789' and A-Z are allowed).", max_length=200)),
                ('title', models.CharField(help_text=b'Human Readable Title', max_length=200)),
                ('abstract', models.CharField(help_text=b'Short Description of Dataset', max_length=2000)),
                ('keep_up_to_date', models.BooleanField(help_text=b'Check this box to keep the dataset up-to-date if changes are made to it on disk or remote server.')),
                ('test_layer', models.CharField(help_text=b'Optional', max_length=200, blank=True)),
                ('test_style', models.CharField(help_text=b'Optional', max_length=200, blank=True)),
                ('display_all_timesteps', models.BooleanField(default=False, help_text=b'Check this box to display each time step in the GetCapabilities document, instead of just the range that the data spans.)')),
                ('latitude_variable', models.CharField(help_text=b'Name of latitude variable. Default: lat', max_length=200, blank=True)),
                ('longitude_variable', models.CharField(help_text=b'Name of longitude variable. Default: lon', max_length=200, blank=True)),
                ('cache_last_updated', models.DateTimeField(null=True, editable=False)),
                ('json', jsonfield.fields.JSONField(help_text=b'Arbitrary dataset-specific json blob', null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('abstract', models.CharField(help_text=b'Short Description of the Group', max_length=2000, blank=True)),
                ('datasets', models.ManyToManyField(help_text=b'Choose the datasets to add to this group, or create a dataset to add to this group', to='wms.Dataset', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Server Title', max_length=1000, blank=True)),
                ('abstract', models.CharField(help_text=b'Server Abstract', max_length=2000, blank=True)),
                ('keywords', models.CharField(help_text=b'Comma Separated List of Keywords', max_length=2000, blank=True)),
                ('contact_person', models.CharField(help_text=b'Person to Contact (Optional)', max_length=1000, blank=True)),
                ('contact_organization', models.CharField(help_text=b'Contact Organization (Optional)', max_length=1000, blank=True)),
                ('contact_position', models.CharField(help_text=b'Contact Position (Optional)', max_length=1000, blank=True)),
                ('contact_street_address', models.CharField(help_text=b'Street Address (Optional)', max_length=1000, blank=True)),
                ('contact_city_address', models.CharField(help_text=b'Address: City (Optional)', max_length=1000, blank=True)),
                ('contact_state_address', models.CharField(help_text=b'Address: State or Providence (Optional)', max_length=1000, blank=True)),
                ('contact_code_address', models.CharField(help_text=b'Address: Postal Code (Optional)', max_length=1000, blank=True)),
                ('contact_country_address', models.CharField(help_text=b'Address: Country (Optional)', max_length=1000, blank=True)),
                ('contact_telephone', models.CharField(help_text=b'Contact Telephone Number (Optional)', max_length=1000, blank=True)),
                ('contact_email', models.CharField(help_text=b'Contact Email Address (Optional)', max_length=1000, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VirtualLayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('layer', models.CharField(help_text=b'Layer designation for the expression', max_length=200)),
                ('layer_expression', models.CharField(help_text=b'Like u,v or Band1*Band2*Band3', max_length=200)),
                ('datasets', models.ManyToManyField(help_text=b'Choose the datasets that this virtual layer applies to', related_name='dataset_lyr_rel', to='wms.Dataset', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
