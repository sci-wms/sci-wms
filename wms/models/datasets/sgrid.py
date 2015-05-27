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

    def has_cache(self):
        raise NotImplementedError

    def update_cache(self, force=False):
        raise NotImplementedError("The SGRID Dataset type is not implemented yet")

    def getmap(self, layer, request):
        raise NotImplementedError

    def getlegendgraphic(self, layer, request):
        raise NotImplementedError

    def getfeatureinfo(self, layer, request):
        raise NotImplementedError

    def wgs84_bounds(self, layer):
        raise NotImplementedError

    def times(self, layer):
        raise NotImplementedError

    def depth_variable(self, layer):
        raise NotImplementedError

    def depth_direction(self, layer):
        raise NotImplementedError

    def depths(self, layer):
        raise NotImplementedError

    def humanize(self):
        return "SGRID"
