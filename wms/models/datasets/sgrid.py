# -*- coding: utf-8 -*-
from datetime import datetime
import bisect
import itertools

import netCDF4 as nc4
import pyproj
import pytz
from pyaxiom.netcdf import EnhancedDataset
from pysgrid import from_nc_dataset
from pysgrid.custom_exceptions import SGridNonCompliantError
from pysgrid.read_netcdf import NetCDFDataset

from wms.models import Dataset


class SGridDataset(Dataset):

    @staticmethod
    def is_valid(uri):
        ds = None
        try:
            ds = EnhancedDataset(uri)
            nc_ds = NetCDFDataset(ds)
            return nc_ds.sgrid_compliant_file()
        except (AttributeError, RuntimeError, SGridNonCompliantError):
            return False
        finally:
            if ds is not None:
                ds.close()

    def update_cache(self, force=False):
        nc = self.netcdf4_dataset()
        sg = from_nc_dataset(nc)
        sg.save_as_netcdf(self.topology_file)
        # add time to the cached topology
        time_vars = nc.get_variables_by_attributes(standard_name='time')
        time_dims = list(itertools.chain.from_iterable([time_var.dimensions for time_var in time_vars]))
        unique_time_dims = list(set(time_dims))
        with EnhancedDataset(self.topology_file, mode='a') as cached_nc:
            # create pertinent time dimensions if they aren't already present
            for unique_time_dim in unique_time_dims:
                dim_size = len(cached_nc.dimensions[unique_time_dim])
                try:
                    cached_nc.createDimension(unique_time_dim, size=dim_size)
                except RuntimeError:
                    continue
            # support cases where there may be more than one variable with standard_name='time' in a dataset
            for time_var in time_vars:
                try:
                    time_var_obj = cached_nc.createVariable(time_var.name, 
                                                            time_var.dtype, 
                                                            time_var.dimensions
                                                            )
                except RuntimeError:
                    time_var_obj = cached_nc.variables[time_var.name]
                finally:
                    time_vals = time_var[:]
                    time_var_obj[:] = time_vals
                    time_var_obj.units = time_var.units
        nc.close()
        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    def getmap(self, layer, request):
        raise NotImplementedError

    def getlegendgraphic(self, layer, request):
        raise NotImplementedError

    def getfeatureinfo(self, layer, request):
        raise NotImplementedError

    def wgs84_bounds(self, layer):
        raise NotImplementedError
    
    def nearest_time(self, layer, time):
        nc = self.topology_dataset()
        time_var = nc.variables['time']
        units = time_var.units
        try:
            calendar = time_var.calendar
        except AttributeError:
            calendar = 'gregorian'
        num_date = round(nc4.date2num(time, units=units, calendar=calendar))
        times = time_var[:]
        time_index = bisect.bisect_right(times, num_date)
        try:
            time_val = times[time_index]
        except IndexError:
            time_index -= 1
            time_val = times[time_index]
        return time_index, time_val
        
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
