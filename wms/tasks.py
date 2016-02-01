# -*- coding: utf-8 -*-
from __future__ import absolute_import
from collections import namedtuple

from datetime import datetime, timedelta
import pytz

from celery import shared_task, group
from django.db.utils import IntegrityError

from wms.models import Dataset, UnidentifiedDataset

from sciwms.utils import single_job_instance, bound_pk_lock, pk_lock


@shared_task(bind=True, default_retry_delay=300)
@bound_pk_lock(timeout=1200)
def process_layers(self, pkey):
    try:
        d = Dataset.objects.get(pk=pkey)
        if hasattr(d, 'process_layers'):
            d.process_layers()
        return 'Processed {} ({!s})'.format(d.name, d.pk)
    except Dataset.DoesNotExist:
        return 'Dataset did not exist, can not complete task'
    except BaseException as e:
        self.retry(exc=e)


@shared_task(bind=True, default_retry_delay=300)
@bound_pk_lock(timeout=1200)
def update_cache(self, pkey, **kwargs):
    try:
        d = Dataset.objects.get(pk=pkey)
        if hasattr(d, 'update_cache'):
            d.update_cache(**kwargs)

        # Save without callbacks
        Dataset.objects.filter(pk=pkey).update(cache_last_updated=datetime.utcnow().replace(tzinfo=pytz.utc))
        return 'Updated {} ({!s})'.format(d.name, d.pk)
    except Dataset.DoesNotExist:
        return 'Dataset did not exist, can not complete task'
    except BaseException as e:
        self.retry(exc=e)


@shared_task(bind=True)
@bound_pk_lock(timeout=3000)
def update_dataset(self, pkey, **kwargs):
    try:
        Dataset.objects.filter(pk=pkey).update(update_task=self.request.id)
        group(process_layers.si(pkey), update_cache.si(pkey, **kwargs)).delay()
        return 'Done'
    finally:
        Dataset.objects.filter(pk=pkey).update(update_task='')


@shared_task
@pk_lock(timeout=1200)
def add_unidentified_dataset(pkey):
    try:
        ud = UnidentifiedDataset.objects.get(pk=pkey)
        klass = Dataset.identify(ud.uri)
        if klass is not None:
            try:
                ds = klass.objects.create(name=ud.name, uri=ud.uri)
                ud.delete()
                return 'Added {}'.format(ds.name)
            except IntegrityError:
                msg = 'Could not add dataset, name "{}" already exists'.format(ud.name)
                ud.messages = msg
                ud.save()
                return msg
        else:
            msg = 'No dataset types found to process {}'.format(ud.uri)
            ud.messages = msg
            ud.save()
            return msg
    except UnidentifiedDataset.DoesNotExist:
        return 'UnidentifiedDataset did not exist, can not complete task'


@shared_task
@single_job_instance(timeout=300)
def regulate():
    updates_scheduled = 0

    rightnow = datetime.utcnow().replace(tzinfo=pytz.utc)

    for d in Dataset.objects.all():
        if d.keep_up_to_date is True:
            if not d.cache_last_updated:
                # Hasnt' been udpated - run the update!
                update_dataset.delay(d.pk)
                updates_scheduled += 1
            else:
                run_another_update_after = d.cache_last_updated + timedelta(seconds=d.update_every)
                if rightnow > run_another_update_after:
                    # It is time for an update - run it!
                    update_dataset.delay(d.pk)
                    updates_scheduled += 1

    results = namedtuple('Results', ['updates_scheduled'])
    return results(updates_scheduled=updates_scheduled)
