# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

import pytz
from datetime import datetime, timedelta
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
                        update_delta = timedelta(minute=1)
                        now = datetime.utcnow().replace(tzinfo=pytz.utc)
                        if not d.has_cache():
                            d.update_cache()
                            logger.info('Creating {} successful'.format(d.name))
                        elif d.cache_last_updated and (now - d.cache_last_updated) < update_delta:
                            logger.info('Updating {} skipped. It was just done!'.format(d.name))
                        else:
                            d.update_cache()
                            logger.info('Updating {} successful'.format(d.name))
                    except NotImplementedError:
                        logger.info('Updating {} failed.  Dataset type not implemented.'.format(d.name))
                    except BaseException as e:
                        logger.info('Updating {} failed. {}.'.format(d.name, str(e)))
            except (ProgrammingError, OperationalError):
                pass
