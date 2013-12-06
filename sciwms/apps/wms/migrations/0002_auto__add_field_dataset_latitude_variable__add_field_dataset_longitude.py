# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Dataset.latitude_variable'
        db.add_column('wms_dataset', 'latitude_variable',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
                      keep_default=False)

        # Adding field 'Dataset.longitude_variable'
        db.add_column('wms_dataset', 'longitude_variable',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'Dataset.latitude_variable'
        db.delete_column('wms_dataset', 'latitude_variable')

        # Deleting field 'Dataset.longitude_variable'
        db.delete_column('wms_dataset', 'longitude_variable')

    models = {
        'wms.dataset': {
            'Meta': {'object_name': 'Dataset'},
            'abstract': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'display_all_timesteps': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keep_up_to_date': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'latitude_variable': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'longitude_variable': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'test_layer': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'test_style': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        'wms.group': {
            'Meta': {'object_name': 'Group'},
            'abstract': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wms.Dataset']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'wms.server': {
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'wms.virtuallayer': {
            'Meta': {'object_name': 'VirtualLayer'},
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wms.Dataset']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'layer_expression': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['wms']
