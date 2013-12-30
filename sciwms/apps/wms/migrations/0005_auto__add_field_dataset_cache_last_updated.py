# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Dataset.cache_last_updated'
        db.add_column(u'wms_dataset', 'cache_last_updated',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Dataset.cache_last_updated'
        db.delete_column(u'wms_dataset', 'cache_last_updated')


    models = {
        u'wms.dataset': {
            'Meta': {'object_name': 'Dataset'},
            'abstract': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'cache_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
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