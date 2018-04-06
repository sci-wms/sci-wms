# -*- coding: utf-8 -*-
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save

from wms.tasks import process_layers, update_cache, add_unidentified_dataset
from wms.models import UGridDataset, SGridDataset, RGridDataset, UGridTideDataset, UnidentifiedDataset


def schedule_dataset_update(sender, instance, created, **kwargs):
    if created is True or not instance.has_cache():
        process_layers(instance.pk)
        update_cache(instance.pk)


@receiver(post_save, sender=UnidentifiedDataset)
def identify_unidentified_dataset(sender, instance, created, **kwargs):
    if created is True:
        add_unidentified_dataset(instance.pk)


@receiver(pre_save, sender=UnidentifiedDataset)
def unid_name_or_uri_changed(sender, instance, **kwargs):
    try:
        obj = UnidentifiedDataset.objects.get(pk=instance.pk)
    except UnidentifiedDataset.DoesNotExist:
        pass
    else:
        if obj.name != instance.name:
            add_unidentified_dataset(instance.pk)
        elif obj.uri != instance.uri:
            add_unidentified_dataset(instance.pk)


@receiver(post_save, sender=UGridTideDataset)
def ugrid_tides_dataset_post_save(*args, **kwargs):
    schedule_dataset_update(*args, **kwargs)


@receiver(post_save, sender=UGridDataset)
def ugrid_dataset_post_save(*args, **kwargs):
    schedule_dataset_update(*args, **kwargs)


@receiver(post_save, sender=SGridDataset)
def sgrid_dataset_post_save(*args, **kwargs):
    schedule_dataset_update(*args, **kwargs)


@receiver(post_save, sender=RGridDataset)
def rgrid_dataset_post_save(*args, **kwargs):
    schedule_dataset_update(*args, **kwargs)


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
