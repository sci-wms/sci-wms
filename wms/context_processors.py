# -*- coding: utf-8 -*-

from wms.utils import version


def globals(request):
    return {
        'sciwms_version': version()
    }
