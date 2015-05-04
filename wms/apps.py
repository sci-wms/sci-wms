# -*- coding: utf-8 -*-
from django.apps import AppConfig


class WmsConfig(AppConfig):
    name = 'wms'
    verbose_name = "WMS"

    def ready(self):
        # Initialize signals
        import wms.signals
