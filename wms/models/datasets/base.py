# -*- coding: utf-8 -*-
import os
import glob
from urlparse import urlparse


from django.db import models
from typedmodels.models import TypedModel
from jsonfield import JSONField

from django.conf import settings
from django.http.response import HttpResponse
from autoslug import AutoSlugField
from autoslug.settings import slugify as default_slugify

import numpy as np

from wms.utils import DotDict, calculate_time_windows
from wms.data_handler import blank_canvas
from wms import glg_handler

from wms import logger


def only_underscores(value):
    return default_slugify(value).replace('-', '_')


class Dataset(TypedModel):
    uri = models.CharField(max_length=1000)
    name = models.CharField(max_length=200, unique=True, help_text="Name/ID to use. No special characters or spaces ('_','0123456789' and A-Z are allowed).")
    title = models.CharField(max_length=200, help_text="Human Readable Title")
    abstract = models.CharField(max_length=2000, help_text="Short Description of Dataset")
    keep_up_to_date = models.BooleanField(help_text="Check this box to keep the dataset up-to-date if changes are made to it on disk or remote server.", default=True)
    display_all_timesteps = models.BooleanField(help_text="Check this box to display each time step in the GetCapabilities document, instead of just the range that the data spans.)", default=False)
    cache_last_updated = models.DateTimeField(null=True, editable=False)
    json = JSONField(blank=True, null=True, help_text="Arbitrary dataset-specific json blob")
    slug = AutoSlugField(populate_from='name', slugify=only_underscores)

    def __unicode__(self):
        return self.name

    @classmethod
    def identify(cls, uri):
        def all_subclasses(klass):
            return klass.__subclasses__() + [g for s in klass.__subclasses__()
                                             for g in all_subclasses(s)]
        for x in all_subclasses(cls):
            if hasattr(x, 'is_valid') and x.is_valid(uri) is True:
                return x

    def path(self):
        if urlparse(self.uri).scheme == "" and not self.uri.startswith("/"):
            # We have a relative path, make it absolute to the sciwms directory.
            return str(os.path.realpath(os.path.join(settings.PROJECT_ROOT, self.uri)))
        else:
            return str(self.uri)

    def getmap(self, layer, request):
        raise NotImplementedError

    def getlegendgraphic(self, layer, request):
        try:
            if 'filledcontours' in request.GET['image_type']:
                return glg_handler.filledcontour(request)
            elif 'contours' in request.GET['image_type']:
                return glg_handler.contour(request)
            elif 'vector' in request.GET['image_type']:
                return glg_handler.vector(request)
            else:
                return glg_handler.gradiant(request)
        except BaseException:
            logger.exception("Could not process GetLegendGraphic request")
            raise

    def getfeatureinfo(self, layer, request):
        raise NotImplementedError

    def getmetadata(self, layer, request):
        if request.GET['item'] == 'minmax':
            return self.minmax(layer, request)
        else:
            raise NotImplementedError("GetMetadata '{}' is not yet implemented".format(request.GET['item']))

    def empty_response(self, layer, request, content_type=None):
        """ Abstracted here to support many different empty response types"""
        content_type = content_type or 'image/png'
        if content_type == 'image/png':
            width = request.GET['width']
            height = request.GET['height']
            canvas = blank_canvas(width, height)
            response = HttpResponse(content_type=content_type)
            canvas.print_png(response)
        return response

    def wgs84_bounds(self, layer):
        raise NotImplementedError

    def time_windows(self, layer):
        times = np.unique(self.times(layer))
        return calculate_time_windows(times)

    def time_bounds(self, layer):
        times = self.times(layer)
        try:
            return DotDict(min=times[0], max=times[-1])
        except IndexError:
            return DotDict(min=None, max=None)

    def depth_bounds(self, layer):
        depths = self.depths(layer)
        try:
            return DotDict(min=depths[0], max=depths[-1])
        except IndexError:
            return DotDict(min=None, max=None)

    def depths(self, layer):
        raise NotImplementedError

    def has_cache(self):
        raise NotImplementedError

    def update_cache(self, force=False):
        raise NotImplementedError

    def clear_cache(self):
        cache_file_list = glob.glob(os.path.join(settings.TOPOLOGY_PATH, self.safe_filename + '*'))
        for cache_file in cache_file_list:
            os.remove(cache_file)

    def active_layers(self):
        layers = self.layer_set.prefetch_related('styles').filter(active=True)
        vlayers = self.virtuallayer_set.prefetch_related('styles').filter(active=True)
        return list(layers) + list(vlayers)

    def all_layers(self):
        layers = self.layer_set.prefetch_related('styles').all()
        vlayers = self.virtuallayer_set.prefetch_related('styles').all()
        return sorted(list(layers) + list(vlayers), key=lambda x: x.active, reverse=True)

    @property
    def safe_filename(self):
        return "".join(c for c in self.name if c.isalnum()).rstrip()

    @property
    def online(self):
        return urlparse(self.uri).scheme != ""

    def humanize(self):
        return "Generic Dataset"
