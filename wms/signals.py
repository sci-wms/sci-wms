# -*- coding: utf-8 -*-
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save

from celery import uuid
from wms.tasks import update_dataset, add_unidentified_dataset
from wms.models import UGridDataset, SGridDataset, RGridDataset, UGridTideDataset, UnidentifiedDataset


def schedule_dataset_update(sender, instance, created, **kwargs):
    if created is True or not instance.has_cache():
        update_dataset.delay(instance.pk)


@receiver(post_save, sender=UnidentifiedDataset)
def identify_unidentified_dataset(sender, instance, created, **kwargs):
    if created is True:
        task_id = uuid()
        instance.job_id = task_id
        instance.save()
        add_unidentified_dataset.apply_async(args=(instance.pk,), task_id=task_id)


@receiver(pre_save, sender=UnidentifiedDataset)
def unid_name_or_uri_changed(sender, instance, **kwargs):
    try:
        obj = UnidentifiedDataset.objects.get(pk=instance.pk)
    except UnidentifiedDataset.DoesNotExist:
        pass
    else:
        if obj.name != instance.name:
            add_unidentified_dataset.delay(instance.pk)
        elif obj.uri != instance.uri:
            add_unidentified_dataset.delay(instance.pk)


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
