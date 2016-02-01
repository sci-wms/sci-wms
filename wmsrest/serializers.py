# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from wms.models import VirtualLayer, Dataset, Layer, SGridDataset, UGridDataset, RGridDataset, UGridTideDataset, Variable, Style, UnidentifiedDataset
from wms.utils import split


class VariableSerializer(serializers.ModelSerializer):

    class Meta:
        model = Variable
        fields = ('id',
                  'std_name',
                  'units',
                  'default_min',
                  'default_max',
                  'logscale')


class DefaultStyleField(serializers.RelatedField):

    queryset = Style.objects.all()

    def to_representation(self, value):
        return value.code

    def to_internal_value(self, data):
        image_type, colormap = split(data, '_', maxsplit=1)
        try:
            return Style.objects.get(image_type=image_type, colormap=colormap)
        except Style.DoesNotExist:
            return None


class LayerSerializer(serializers.ModelSerializer):
    styles = serializers.StringRelatedField(many=True, read_only=True)
    default_style = DefaultStyleField(many=False)

    class Meta:
        model = Layer
        fields = ('id',
                  'var_name',
                  'std_name',
                  'units',
                  'description',
                  'active',
                  'styles',
                  'default_min',
                  'default_max',
                  'logscale',
                  'default_style',
                  'default_numcontours')


class VirtualLayerSerializer(serializers.ModelSerializer):
    styles = serializers.StringRelatedField(many=True, read_only=True)
    default_style = DefaultStyleField(many=False)

    class Meta:
        model = VirtualLayer
        fields = ('id',
                  'var_name',
                  'std_name',
                  'units',
                  'description',
                  'active',
                  'styles',
                  'default_min',
                  'default_max',
                  'logscale',
                  'default_style',
                  'default_numcontours')


class UnidentifiedDatasetSerializer(serializers.ModelSerializer):

    name = serializers.CharField(
        validators=[
            UniqueValidator(queryset=UnidentifiedDataset.objects.all()),
            UniqueValidator(queryset=Dataset.objects.all())
        ]
    )

    class Meta:
        model = UnidentifiedDataset
        fields = ('id',
                  'uri',
                  'name',
                  'job_id',
                  'messages')


class DatasetSerializer(serializers.ModelSerializer):
    layer_set = LayerSerializer(many=True, read_only=True)
    virtuallayer_set = VirtualLayerSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ('id',
                  'uri',
                  'type',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'update_every',
                  'display_all_timesteps',
                  'cache_last_updated',
                  'layer_set',
                  'virtuallayer_set')


class UGridDatasetSerializer(serializers.ModelSerializer):
    layer_set = LayerSerializer(many=True, read_only=True)
    virtuallayer_set = VirtualLayerSerializer(many=True, read_only=True)

    class Meta:
        model = UGridDataset
        fields = ('id',
                  'uri',
                  'type',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'update_every',
                  'display_all_timesteps',
                  'cache_last_updated',
                  'layer_set',
                  'virtuallayer_set')


class SGridDatasetSerializer(serializers.ModelSerializer):
    layer_set = LayerSerializer(many=True, read_only=True)
    virtuallayer_set = VirtualLayerSerializer(many=True, read_only=True)

    class Meta:
        model = SGridDataset
        fields = ('id',
                  'uri',
                  'type',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'update_every',
                  'display_all_timesteps',
                  'cache_last_updated',
                  'layer_set',
                  'virtuallayer_set')


class RGridDatasetSerializer(serializers.ModelSerializer):
    layer_set = LayerSerializer(many=True, read_only=True)
    virtuallayer_set = VirtualLayerSerializer(many=True, read_only=True)

    class Meta:
        model = RGridDataset
        fields = ('id',
                  'uri',
                  'type',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'update_every',
                  'display_all_timesteps',
                  'cache_last_updated',
                  'layer_set',
                  'virtuallayer_set')


class UGridTideDatasetSerializer(serializers.ModelSerializer):
    layer_set = LayerSerializer(many=True, read_only=True)
    virtuallayer_set = VirtualLayerSerializer(many=True, read_only=True)

    class Meta:
        model = UGridTideDataset
        fields = ('id',
                  'uri',
                  'type',
                  'name',
                  'title',
                  'abstract',
                  'keep_up_to_date',
                  'update_every',
                  'display_all_timesteps',
                  'cache_last_updated',
                  'layer_set',
                  'virtuallayer_set')
