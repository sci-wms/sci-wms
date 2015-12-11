# -*- coding: utf-8 -*-
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from wms.models import UGridDataset, SGridDataset, RGridDataset, UGridTideDataset


@receiver(post_save, sender=UGridTideDataset)
def ugrid_tides_dataset_post_save(sender, instance, created, **kwargs):
    if settings.TESTING is not True:
        instance.process_layers()
        if created is True or not instance.has_cache():
            instance.update_cache()


@receiver(post_save, sender=UGridDataset)
def ugrid_dataset_post_save(sender, instance, created, **kwargs):
    if settings.TESTING is not True:
        instance.process_layers()
        if created is True or not instance.has_cache():
            instance.update_cache()


@receiver(post_save, sender=SGridDataset)
def sgrid_dataset_post_save(sender, instance, created, **kwargs):
    if settings.TESTING is not True:
        instance.process_layers()
        if created is True or not instance.has_cache():
            instance.update_cache()


@receiver(post_save, sender=RGridDataset)
def rgrid_dataset_post_save(sender, instance, created, **kwargs):
    if settings.TESTING is not True:
        instance.process_layers()
        if created is True or not instance.has_cache():
            instance.update_cache()


@receiver(post_delete, sender=UGridTideDataset)
def ugrid_tide_dataset_post_delete(sender, instance, **kwargs):
    instance.clear_cache()


@receiver(post_delete, sender=UGridDataset)
def ugrid_dataset_post_delete(sender, instance, **kwargs):
    instance.clear_cache()


@receiver(post_delete, sender=SGridDataset)
def sgrid_dataset_post_delete(sender, instance, **kwargs):
    instance.clear_cache()


@receiver(post_delete, sender=RGridDataset)
def rgrid_dataset_post_delete(sender, instance, **kwargs):
    instance.clear_cache()
