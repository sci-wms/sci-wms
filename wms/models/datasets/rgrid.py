# -*- coding: utf-8 -*-
from sciwms.apps.wms.models import Dataset


class RGridDataset(Dataset):
    def update_cache(self, force=False):
        raise NotImplementedError("The RGRID Dataset type is not implemented yet")
