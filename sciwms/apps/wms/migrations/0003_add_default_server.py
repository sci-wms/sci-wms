# -*- coding: utf-8 -*-
from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        """ Add default Server object """
        if (len(orm.Server.objects.all()) < 1):
            s = orm.Server(title="Sci-wms Server")
            s.save()

    def backwards(self, orm):
        """ Remove the default instance if it is the only one """
        pass

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
    symmetrical = True
