# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

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
            try:
                for d in Dataset.objects.all():
                    try:
                        if not d.has_cache():
                            logger.info('Creating {} successful'.format(d.name))
                        else:
                            logger.info('Updating {} successful'.format(d.name))
                        d.update_cache()
                    except NotImplementedError:
                        logger.info('Updating {} failed.  Dataset type not implemented.'.format(d.name))
                    except BaseException as e:
                        logger.info('Updating {} failed. {}.'.format(d.name, str(e)))
            except (ProgrammingError, OperationalError):
                pass
