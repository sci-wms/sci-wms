#!python
# coding=utf-8
from django.apps import AppConfig


class WmsConfig(AppConfig):
    name = 'wms'
    verbose_name = "WMS"

    def ready(self):
        # Initialize signals
        import wms.signals  # noqa

        # Load cmocean colormaps
        import cmocean
        import matplotlib.cm
        for n, m in cmocean.cm.cmap_d.items():
            matplotlib.cm.register_cmap(name=n, cmap=m)
