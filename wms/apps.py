# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings

from wms import logger


class WmsConfig(AppConfig):
    name = 'wms'
    verbose_name = "WMS"

    def ready(self):
        # Initialize signals
        import wms.signals

        Dataset = self.get_model('Dataset')
        if settings.TESTING or settings.DEBUG:
            logger.info("Not updating datasets due to TESTING or DEBUG setting being True")
        else:
            for d in Dataset.objects.all():
                try:
                    d.update_cache()
                    logger.info('Updating {} successful'.format(d.name))
                except NotImplementedError:
                    logger.info('Updating {} failed.  Dataset type not implemented.'.format(d.name))
                except BaseException as e:
                    logger.info('Updating {} failed. {}.'.format(d.name, str(e)))
