# -*- coding: utf-8 -*-
from wms.models import Dataset


class RGridDataset(Dataset):
    def update_cache(self, force=False):
        raise NotImplementedError("The RGRID Dataset type is not implemented yet")

    def humanize(self):
        return "RGRID"
