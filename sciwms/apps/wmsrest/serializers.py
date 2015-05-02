# -*- coding: utf-8 -*-
from rest_framework import serializers
from sciwms.apps.wms.models import VirtualLayer, Dataset, Layer, SGridDataset, UGridDataset


class LayerSerializer(serializers.ModelSerializer):
    styles = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Layer
        fields = ('var_name', 'std_name', 'description', 'active', 'styles', 'default_min', 'default_max')


class VirtualLayerSerializer(serializers.ModelSerializer):
    styles = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = VirtualLayer
        fields = ('var_name', 'std_name', 'description', 'active', 'styles', 'default_min', 'default_max')


class DatasetSerializer(serializers.ModelSerializer):
    layer_set = LayerSerializer(many=True, read_only=True)
    virtuallayer_set = VirtualLayerSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ('uri',
                  'type',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'display_all_timesteps',
                  'layer_set',
                  'virtuallayer_set')


class UGridDatasetSerializer(serializers.ModelSerializer):
    layer_set = LayerSerializer(many=True, read_only=True)
    virtuallayer_set = VirtualLayerSerializer(many=True, read_only=True)

    class Meta:
        model = UGridDataset
        fields = ('uri',
                  'type',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'display_all_timesteps',
                  'layer_set',
                  'virtuallayer_set')


class SGridDatasetSerializer(serializers.ModelSerializer):
    layer_set = LayerSerializer(many=True, read_only=True)
    virtuallayer_set = VirtualLayerSerializer(many=True, read_only=True)

    class Meta:
        model = SGridDataset
        fields = ('uri',
                  'type',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'display_all_timesteps',
                  'layer_set',
                  'virtuallayer_set')
