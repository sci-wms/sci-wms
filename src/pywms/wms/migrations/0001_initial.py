# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Dataset'
        db.create_table('wms_dataset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uri', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('abstract', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('keep_up_to_date', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('test_layer', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('test_style', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('display_all_timesteps', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('wms', ['Dataset'])

        # Adding model 'VirtualLayer'
        db.create_table('wms_virtuallayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('layer', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('layer_expression', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('wms', ['VirtualLayer'])

        # Adding M2M table for field datasets on 'VirtualLayer'
        m2m_table_name = db.shorten_name('wms_virtuallayer_datasets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('virtuallayer', models.ForeignKey(orm['wms.virtuallayer'], null=False)),
            ('dataset', models.ForeignKey(orm['wms.dataset'], null=False))
        ))
        db.create_unique(m2m_table_name, ['virtuallayer_id', 'dataset_id'])

        # Adding model 'Group'
        db.create_table('wms_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('abstract', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
        ))
        db.send_create_signal('wms', ['Group'])

        # Adding M2M table for field datasets on 'Group'
        m2m_table_name = db.shorten_name('wms_group_datasets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['wms.group'], null=False)),
            ('dataset', models.ForeignKey(orm['wms.dataset'], null=False))
        ))
        db.create_unique(m2m_table_name, ['group_id', 'dataset_id'])

        # Adding model 'Server'
        db.create_table('wms_server', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('abstract', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('contact_person', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_organization', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_position', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_street_address', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_city_address', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_state_address', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_code_address', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_country_address', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_telephone', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('contact_email', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
        ))
        db.send_create_signal('wms', ['Server'])


    def backwards(self, orm):
        # Deleting model 'Dataset'
        db.delete_table('wms_dataset')

        # Deleting model 'VirtualLayer'
        db.delete_table('wms_virtuallayer')

        # Removing M2M table for field datasets on 'VirtualLayer'
        db.delete_table(db.shorten_name('wms_virtuallayer_datasets'))

        # Deleting model 'Group'
        db.delete_table('wms_group')

        # Removing M2M table for field datasets on 'Group'
        db.delete_table(db.shorten_name('wms_group_datasets'))

        # Deleting model 'Server'
        db.delete_table('wms_server')


    models = {
        'wms.dataset': {
            'Meta': {'object_name': 'Dataset'},
            'abstract': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'display_all_timesteps': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keep_up_to_date': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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