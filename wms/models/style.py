# -*- coding: utf-8 -*-
from django.db import models
import matplotlib.cm


class Style(models.Model):
    description = models.CharField(max_length=200, blank=True, help_text="Descriptive name of this style, optional")
    colormap    = models.CharField(max_length=200,
                                   help_text="The matplotlib colormaps. See: http://matplotlib.org/1.2.1/examples/pylab_examples/show_colormaps.html.",
                                   choices=sorted((m, m) for m in matplotlib.cm.cmap_d.keys() if not m.endswith("_r")))
    image_type  = models.CharField(max_length=200, default="filledcontours", choices=(("filledcontours", "filledcontours"),
                                                                                      ("contours", "contours"),
                                                                                      ("filledhatches", "filledhatches"),
                                                                                      ("hatches", "hatches"),
                                                                                      ("pcolor", "pcolor"),
                                                                                      ("vectors", "vectors")))

    @classmethod
    def defaults(cls):
        return Style.objects.filter(colormap='cubehelix', image_type__in=['filledcontours', 'contours', 'filledhatches', 'hatches', 'pcolor'])

    @property
    def code(self):
        return '{}_{}'.format(self.image_type, self.colormap)

    def __str__(self):
        return '{}_{}'.format(self.image_type, self.colormap)
