# -*- coding: utf-8 -*-
import os

from wms.models import Dataset


class RGridDataset(Dataset):

    def has_cache(self):
        return os.path.exists(self.topology_file)

    def update_cache(self, force=False):
        raise NotImplementedError("The RGRID Dataset type is not implemented yet")

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
        return "RGRID"
