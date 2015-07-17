# -*- coding: utf-8 -*-
from django.db import models


class Variable(models.Model):
    std_name    = models.CharField(max_length=200, help_text="The 'standard_name' of this variable")
    units       = models.CharField(max_length=200, blank=True, help_text="The 'units' of this variable")
    logscale    = models.NullBooleanField(default=None, null=True, help_text="If this variable should default to a log scale")
    default_min = models.FloatField(null=True, default=None, blank=True, help_text="If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.")
    default_max = models.FloatField(null=True, default=None, blank=True, help_text="If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.")

    class Meta:
        unique_together = ('std_name', 'units',)

    def __unicode__(self):
        return '{}_{}'.format(self.std_name, self.units)
