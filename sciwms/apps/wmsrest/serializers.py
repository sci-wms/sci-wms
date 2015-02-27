'''
Created on Feb 12, 2015

@author: ayan
'''
from rest_framework import serializers
from sciwms.apps.wms.models import VirtualLayer, Dataset


class DatasetSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Dataset
        fields = ('uri',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'id',
                  'dataset_lyr_rel',
                  'display_all_timesteps'
                  )


class VirtualLayerSerializer(serializers.ModelSerializer):
    datasets = serializers.PrimaryKeyRelatedField(many=True, queryset=Dataset.objects.all())
    
    class Meta:
        model = VirtualLayer
        fields = ('layer',
                  'layer_expression',
                  'datasets',
                  'id'
                  )