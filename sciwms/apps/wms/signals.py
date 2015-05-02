from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

from sciwms.apps.wms.models import UGridDataset, SGridDataset


@receiver(post_save, sender=SGridDataset)
def ugrid_dataset_post_save(sender, instance, created, **kwargs):
    if created is True and settings.TESTING is not True:
        instance.update_cache()
        instance.process_layers()


@receiver(post_save, sender=UGridDataset)
def sgrid_dataset_post_save(sender, instance, created, **kwargs):
    if created is True and settings.TESTING is not True:
        instance.update_cache()
        instance.process_layers()
