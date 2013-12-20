# -*- coding: utf-8 -*-
import os

from django.db import models
from django.conf import settings

from south.db import db
from south.v2 import DataMigration
from south.utils import datetime_utils as datetime

resource_path = os.path.join(settings.PROJECT_ROOT, 'apps', 'wms', 'resources')


class Migration(DataMigration):

    def forwards(self, orm):
        """ Add default Dataset and VirtualLayer objects """

        d1 = orm.Dataset(uri                   = os.path.join(resource_path, "nasa_scb20111015.nc"),
                         name                  = "CGridTest",
                         title                 = "CGrid Test dataset",
                         abstract              = "CGrid Test data set for sci-wms",
                         display_all_timesteps = False,
                         keep_up_to_date       = False,
                         test_layer            = "u,v",
                         test_style            = "pcolor_average_jet_None_None_cell_False" )
        d1.save()

        d2 = orm.Dataset(uri                   = os.path.join(resource_path, "201220109.nc"),
                         name                  = "UGridTest",
                         title                 = "UGrid Test dataset",
                         abstract              = "UGrid Test data set for sci-wms",
                         display_all_timesteps = False,
                         keep_up_to_date       = False,
                         test_layer            = "u,v",
                         test_style            = "pcolor_average_jet_None_None_cell_False" )
        d2.save()

        uv = orm.VirtualLayer(layer="U,V vectors", layer_expression="u,v")
        uv.save()
        uv.datasets.add(d1)
        uv.datasets.add(d2)
        uv.save()

        bands = orm.VirtualLayer(layer="RGB Band Images", layer_expression="Band1*Band2*Band3")
        bands.save()

    def backwards(self, orm):
        """ Remove the default instance if it is the only one """
        pass

    models = {
        u'wms.dataset': {
            'Meta': {'object_name': 'Dataset'},
            'abstract': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'display_all_timesteps': ('django.db.models.fields.BooleanField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keep_up_to_date': ('django.db.models.fields.BooleanField', [], {}),
            'latitude_variable': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'longitude_variable': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'test_layer': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'test_style': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'wms.group': {
            'Meta': {'object_name': 'Group'},
            'abstract': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['wms.Dataset']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'wms.server': {
            'Meta': {'object_name': 'Server'},
            'abstract': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'contact_city_address': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_code_address': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_country_address': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_email': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_organization': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_person': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_position': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_state_address': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_street_address': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'contact_telephone': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'})
        },
        u'wms.virtuallayer': {
            'Meta': {'object_name': 'VirtualLayer'},
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['wms.Dataset']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'layer_expression': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['wms']
    symmetrical = True
