# -*- coding: utf-8 -*-
from wms.models import Dataset

from pyaxiom.netcdf import EnhancedDataset


class SGridDataset(Dataset):

    @staticmethod
    def is_valid(uri):
        ds = None
        try:
            ds = EnhancedDataset(uri)
            return 'sgrid' in ds.Conventions.lower()
        except (AttributeError, RuntimeError):
            return False
        finally:
            if ds is not None:
                ds.close()

    def update_cache(self, force=False):
        raise NotImplementedError("The SGRID Dataset type is not implemented yet")

    def humanize(self):
        return "SGRID"
