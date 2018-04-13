# -*- coding: utf-8 -*-
from wms.models import Dataset, NetCDFDataset


class RGridDataset(Dataset, NetCDFDataset):

    def has_grid_cache(self):
        raise NotImplementedError

    def has_time_cache(self):
        raise NotImplementedError

    def update_time_cache(self):
        raise NotImplementedError("The RGRID Dataset type is not implemented yet")

    def update_grid_cache(self):
        raise NotImplementedError("The RGRID Dataset type is not implemented yet")

    def minmax(self, layer, request):
        raise NotImplementedError

    def getmap(self, layer, request):
        raise NotImplementedError

    def getlegendgraphic(self, layer, request):
        raise NotImplementedError

    def getfeatureinfo(self, layer, request):
        raise NotImplementedError

    def wgs84_bounds(self, layer):
        raise NotImplementedError

    def nearest_z(self, layer, z):
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
        return "RGRID"
