# -*- coding: utf-8 -*-
import os
from datetime import datetime

import pytz

from pyugrid import UGrid
from pyaxiom.netcdf import EnhancedDataset

from wms.models import Dataset
from sciwms import logger


class UGridDataset(Dataset):

    @staticmethod
    def is_valid(uri):
        ds = None
        try:
            ds = EnhancedDataset(uri)
            return 'ugrid' in ds.Conventions.lower()
        except (AttributeError, RuntimeError):
            return False
        finally:
            if ds is not None:
                ds.close()

    def update_cache(self, force=False):
        try:
            nc = self.netcdf4_dataset()
            ug = UGrid.from_nc_dataset(nc=nc)
            ug.save_as_netcdf(self.topology_file)

            if not os.path.exists(self.topology_file):
                logger.error("Failed to create topology_file cache for Dataset '{}'".format(self.dataset))
                return

            cached_nc = EnhancedDataset(self.topology_file, mode='a')

            # add time to the cached topology
            time_var = nc.get_variables_by_attributes(standard_name='time')[0]
            time_vals = time_var[:]
            if time_vals is not None:
                cached_nc.createDimension('time', size=time_vals.size)
                if time_vals.ndim > 1:  # deal with one dimensional time for now
                    pass
                else:
                    cached_time_var = cached_nc.createVariable(varname='time',
                                                               datatype='f8',
                                                               dimensions=('time',))
                    cached_time_var[:] = time_vals[:]
                    cached_time_var.units = time_var.units
            cached_nc.close()
        except:
            raise
        finally:
            if nc is not None:
                nc.close()

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    def humanize(self):
        return "UGRID"
