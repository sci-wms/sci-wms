# -*- coding: utf-8 -*-
from django.db import models
import matplotlib.pyplot as plt


class Style(models.Model):
    description = models.CharField(max_length=200, blank=True, help_text="Descriptive name of this style, optional")
    colormap    = models.CharField(max_length=200,
                                   help_text="The matplotlib colormaps. See: http://matplotlib.org/1.2.1/examples/pylab_examples/show_colormaps.html.",
                                   choices=sorted((m, m) for m in plt.cm.datad if not m.endswith("_r")))
    image_type  = models.CharField(max_length=200, default="filledcontours", choices=(("filledcontours", "filledcontours"),
                                                                                      ("contours", "contours"),
                                                                                      ("pcolor", "pcolor"),
                                                                                      ("facets", "facets"),
                                                                                      ("composite", "composite"),
                                                                                      ("vectors", "vectors"),
                                                                                      ("barbs", "barbs")))

    @classmethod
    def defaults(cls):
        return Style.objects.filter(colormap='jet', image_type__in=['filledcontours', 'contours', 'facets', 'pcolor'])

    @property
    def code(self):
        return '{}_{}'.format(self.image_type, self.colormap)

    def __unicode__(self):
        return '{}_{}'.format(self.image_type, self.colormap)
