from django.dispatch import receiver
from django.db.models.signals import post_save

from sciwms.apps.wms.models import Dataset


@receiver(post_save, sender=Dataset)
def dataset_post_save(sender, instance, created, **kwargs):
    if created is True:
        instance.update_cache()
