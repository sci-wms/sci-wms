# -*- coding: utf-8 -*-
import re

from django.db import models

from wms.models import Style, Variable
from wms.utils import DotDict

from wms.utils import split
from wms import logger


class LayerBase(models.Model):
    var_name    = models.CharField(max_length=200, help_text="Variable name from dataset")
    std_name    = models.CharField(max_length=200, blank=True, help_text="The 'standard_name' from the dataset variable")
    units       = models.CharField(max_length=200, blank=True, help_text="The 'units' from the dataset variable")
    logscale    = models.NullBooleanField(default=None, null=True, help_text="If this dataset variable should default to a log scale")
    description = models.CharField(max_length=200, blank=True, help_text="Descriptive name of this layer, optional")
    dataset     = models.ForeignKey('Dataset')
    active      = models.BooleanField(default=False)
    styles      = models.ManyToManyField('Style')
    default_min = models.FloatField(null=True, default=None, blank=True, help_text="If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.")
    default_max = models.FloatField(null=True, default=None, blank=True, help_text="If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.")
    default_numcontours = models.IntegerField(default=20)

    class Meta:
        abstract = True
        ordering = ('var_name',)

    @property
    def access_name(self):
        return self.var_name

    @property
    def all_styles(self):
        return list(set(self.styles.all()).union(set([self.default_style])))

    @property
    def defaults(self):

        lmin = self.default_min
        lmax = self.default_max
        llog = self.logscale

        default = Variable.objects.filter(std_name=self.std_name, units=self.units).first()
        if default:
            if lmin is None and default.default_min:
                lmin = default.default_min
            if lmax is None and default.default_max:
                lmax = default.default_max
            if llog is None and default.logscale is not None:
                llog = default.logscale

        image_type, colormap = split(self.default_style.code, '_', maxsplit=1)

        return DotDict(min=lmin, max=lmax, logscale=llog, image_type=image_type, colormap=colormap, numcontours=self.default_numcontours)

    def __str__(self):
        z = self.var_name
        z += ' ({})'.format(self.std_name) if self.std_name else ''
        z += ' - Active: {}'.format(self.active)
        return z


def get_default_layer_style():
    try:
        return Style.objects.get(image_type='filledcontours', colormap='cubehelix').pk
    except Style.DoesNotExist:
        return 1


def get_default_vlayer_style():
    try:
        return Style.objects.get(image_type='vectors', colormap='cubehelix').pk
    except Style.DoesNotExist:
        return 1


class Layer(LayerBase):

    default_style = models.ForeignKey('Style', on_delete=models.SET_DEFAULT, null=False, related_name='l_default_style', default=get_default_layer_style)

    def wgs84_bounds(self):
        return self.dataset.wgs84_bounds(self)

    def time_windows(self):
        return self.dataset.time_windows(self)

    def time_bounds(self):
        return self.dataset.time_bounds(self)

    def times(self):
        return self.dataset.times(self)

    def depth_bounds(self):
        return self.dataset.depth_bounds(self)

    def depth_direction(self):
        return self.dataset.depth_direction(self)

    def depths(self):
        return self.dataset.depths(self)

    @property
    def layers(self):
        return self.dataset.layer_set.filter(var_name=self.var_name)


class VirtualLayer(LayerBase):

    default_style = models.ForeignKey('Style', on_delete=models.SET_DEFAULT, null=False, related_name='vl_default_style', default=get_default_vlayer_style)

    @classmethod
    def make_vector_layer(cls, us, vs, std_name, style, dataset_id):
        for u in us:
            u_match = '_'.join([ x for x in u.standard_name.split('_') if x not in ['x', 'eastward']])
            for v in vs:
                v_match = '_'.join([ x for x in v.standard_name.split('_') if x not in ['y', 'northward']])

                if u_match == v_match:
                    if hasattr(u, 'units'):
                        units = u.units
                    elif hasattr(v, 'units'):
                        units = v.units
                    else:
                        units = None
                    try:
                        vl, created = VirtualLayer.objects.get_or_create(var_name='{},{}'.format(u._name, v._name),
                                                                         dataset_id=dataset_id)
                        vl.std_name = std_name
                        vl.units = units
                        vl.description = "U ({}) and V ({}) vectors".format(u._name, v._name)

                        if created is True:
                            vl.active = True
                            vl.styles.add(Style.objects.get(colormap='cubehelix', image_type=style))

                        vl.save()
                        break
                    except:
                        raise

    @property
    def access_name(self):
        try:
            return self.single_layer.var_name
        except AttributeError:
            return re.findall(r"[^*,]+", self.var_name)[0]

    @property
    def single_layer(self):
        single_var = re.findall(r"[^*,]+", self.var_name)[0]
        return self.dataset.layer_set.filter(var_name=single_var).first()

    @property
    def layers(self):
        all_vars = re.findall(r"[^*,]+", self.var_name)
        return self.dataset.layer_set.filter(var_name__in=all_vars)

    def wgs84_bounds(self):
        return self.dataset.wgs84_bounds(self.single_layer)

    def time_windows(self):
        return self.dataset.time_windows(self.single_layer)

    def time_bounds(self):
        return self.dataset.time_bounds(self.single_layer)

    def times(self):
        return self.dataset.times(self.single_layer)

    def depth_bounds(self):
        return self.dataset.depth_bounds(self.single_layer)

    def depth_direction(self):
        return self.dataset.depth_direction(self.single_layer)

    def depths(self):
        return self.dataset.depths(self.single_layer)
