# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger('sci-wms')

from .celery import app as celery_app  # noqa

__all__ = ['celery_app']
