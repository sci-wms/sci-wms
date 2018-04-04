#!python
# coding=utf-8
from functools import wraps

from django.core.cache import caches

from sciwms import logger  # noqa


def acquire(lock_id, timeout):
    caches['default'].add(lock_id, 'true', timeout)


def release(lock_id):
    caches['default'].delete(lock_id)


def single_job_instance(timeout):
    def task_exc(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = 'single_job_instance-lock-{0}'.format(func.__name__)
            if acquire(lock_id, timeout):
                try:
                    return func(*args, **kwargs)
                finally:
                    release(lock_id)
            else:
                logger.warning('{0} is already being run by another worker. Skipping.'.format(func.__name__))
        return wrapper
    return task_exc


def bound_pk_lock(timeout):
    def task_exc(func):
        @wraps(func)
        def wrapper(f, *args, **kwargs):
            pk = args[0]
            lock_id = '{0}-lock-{1}'.format(f.__name__, pk)
            if acquire(lock_id, timeout):
                try:
                    return func(f, *args, **kwargs)
                finally:
                    release(lock_id)
            else:
                logger.warning('{0} with pk {1} is already being run by another worker. Skipping.'.format(func.__name__, pk))
        return wrapper
    return task_exc


def pk_lock(timeout):
    def task_exc(func):
        @wraps(func)
        def wrapper(pk, *args, **kwargs):
            lock_id = '{0}-lock-{1}'.format(func.__name__, pk)
            if acquire(lock_id, timeout):
                try:
                    return func(pk, *args, **kwargs)
                finally:
                    release(lock_id)
            else:
                logger.warning('{0} with pk {1} is already being run by another worker. Skipping.'.format(func.__name__, pk))
        return wrapper
    return task_exc


def stringify_list(thing):
    if isinstance(thing, (list, tuple)):
        return str(thing)
    return thing
