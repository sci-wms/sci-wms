# -*- coding: utf-8 -*-
from django.db import models


class Group(models.Model):
    name = models.CharField(max_length=200)
    abstract = models.CharField(max_length=2000, blank=True, help_text="Short Description of the Group")
    datasets = models.ManyToManyField('wms.Dataset', blank=True, help_text="Choose the datasets to add to this group, or create a dataset to add to this group")

    def __unicode__(self):
        return self.name
