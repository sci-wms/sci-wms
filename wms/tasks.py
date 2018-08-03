# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime, timedelta

import pytz
from huey import crontab
from huey.contrib.djhuey import HUEY

from django.db.utils import IntegrityError

from wms.models import Dataset, UnidentifiedDataset
from huey.contrib.djhuey import db_periodic_task, db_task

from sciwms import logger  # noqa


@db_task()
def update_layers(pkey):
    with HUEY.lock_task('process-{}'.format(pkey)):
        try:
            d = Dataset.objects.get(pk=pkey)
            d.update_layers()
            return 'Processed {} ({!s})'.format(d.name, d.pk)
        except Dataset.DoesNotExist:
            return 'Dataset did not exist, can not complete task'
        except AttributeError:
            return 'No update_layers method on this dataset'


@db_task()
def update_time_cache(pkey):
    with HUEY.lock_task('time-cache-{}'.format(pkey)):
        try:
            d = Dataset.objects.get(pk=pkey)
            d.update_time_cache()
            # Save without callbacks
            Dataset.objects.filter(pk=pkey).update(cache_last_updated=datetime.utcnow().replace(tzinfo=pytz.utc))
            return 'Updated {} ({!s})'.format(d.name, d.pk)
        except Dataset.DoesNotExist:
            return 'Dataset did not exist, can not complete task'
        except AttributeError:
            return 'No update_time_cache method on this dataset'


@db_task()
def update_grid_cache(pkey):
    with HUEY.lock_task('grid-cache-{}'.format(pkey)):
        try:
            d = Dataset.objects.get(pk=pkey)
            d.update_grid_cache()
            return 'Updated {} ({!s})'.format(d.name, d.pk)
        except Dataset.DoesNotExist:
            return 'Dataset did not exist, can not complete task'
        except AttributeError:
            return 'No update_grid_cache method on this dataset'


@db_task()
def update_dataset(pkey):
    with HUEY.lock_task('updating-{}'.format(pkey)):
        try:
            Dataset.objects.filter(pk=pkey).update(update_task='UPDATING')
            update_layers(pkey)
            update_time_cache(pkey)
            update_grid_cache(pkey)
            return 'Done'
        finally:
            Dataset.objects.filter(pk=pkey).update(update_task='')


@db_task()
def add_unidentified_dataset(pkey):
    with HUEY.lock_task('unidentified-{}'.format(pkey)):
        try:
            ud = UnidentifiedDataset.objects.get(pk=pkey)
            klass = Dataset.identify(ud.uri)
            if klass is not None:
                try:
                    ud.delete()
                    ds = klass.objects.create(name=ud.name, uri=ud.uri)
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


@db_periodic_task(crontab(minute='10'))
@HUEY.lock_task('regulate')
def regulate():
    updates_scheduled = 0

    rightnow = datetime.utcnow().replace(tzinfo=pytz.utc)

    for d in Dataset.objects.all():
        if d.keep_up_to_date is True:
            if not d.cache_last_updated:
                # Hasnt' been udpated - run the update!
                update_layers(d.pkey)
                update_time_cache(d.pkey)
                updates_scheduled += 1
            else:
                run_another_update_after = d.cache_last_updated + timedelta(seconds=d.update_every)
                if rightnow > run_another_update_after:
                    # It is time for an update - run it!
                    update_layers(d.pkey)
                    update_time_cache(d.pkey)
                    updates_scheduled += 1

    results = namedtuple('Results', ['updates_scheduled'])
    return results(updates_scheduled=updates_scheduled)
