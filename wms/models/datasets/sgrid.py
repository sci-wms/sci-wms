# -*- coding: utf-8 -*-
from wms.models import Dataset


class SGridDataset(Dataset):
    def update_cache(self, force=False):
        raise NotImplementedError("The SGRID Dataset type is not implemented yet")
