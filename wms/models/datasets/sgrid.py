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

from wms.data_handler import lat_lon_subset_idx
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
        time_index, time_value = self.nearest_time(layer, request.GET['time'])
        epsg_4326 = pyproj.Proj(init='EPSG:4326')
        bbox = request.GET['bbox']
        requested_crs = request.GET['crs']
        wgs84_minx, wgs84_miny = pyproj.transform(requested_crs, epsg_4326, bbox.minx, bbox.miny)
        wgs84_maxx, wgs84_maxy = pyproj.transform(requested_crs, epsg_4326, bbox.maxx, bbox.maxx)
        nc  = self.netcdf4_dataset()
        cached_sg = from_nc_dataset(self.topology_file)
        lon_name, lat_name = cached_sg.face_coordiates
        lon_obj = getattr(cached_sg, lon_name)
        lat_obj = getattr(cached_sg, lat_name)
        centers = cached_sg.centers
        lon = centers[..., 0][lon_obj.center_slicing]
        lat = centers[..., 1][lat_obj.center_slicing]
        spatial_idx = lat_lon_subset_idx(lon, lat, 
                                         lonmin=wgs84_minx, 
                                         latmin=wgs84_miny, 
                                         lonmax=wgs84_maxx, 
                                         latmax=wgs84_maxy
                                         )
        subset_lon = self._spatial_data_subset(lon, spatial_idx)
        subset_lat = self._spatial_data_subset(lat, spatial_idx)
        lyr_access_name = layer.access_name
        split_lyr_vars = lyr_access_name.split(',')
        lyr_vars = {}
        for var_idx, var_name in enumerate(split_lyr_vars):
            lv_key = 'var{0}'.format(var_idx)
            lyr_vars[lv_key] = var_name
        if len(lyr_vars) == 2:
            var0_name = lyr_vars['var0']
            var1_name = lyr_vars['var1']
            var0_obj = getattr(cached_sg, var0_name)
            var1_obj = getattr(cached_sg, var1_name)
            raw_var0 = nc.variables[var0_name]
            raw_var1 = nc.variables[var1_name]
            
    def getlegendgraphic(self, layer, request):
        raise NotImplementedError

    def getfeatureinfo(self, layer, request):
        raise NotImplementedError

    def wgs84_bounds(self, layer):
        raise NotImplementedError
    
    def nearest_time(self, layer, time):
        """
        Very similar to ugrid
        
        """
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
    
    def nearest_z(self, layer, z):
        """
        Return the z index and z value that is closest
        
        """
        raise NotImplementedError
        
        
    def times(self, layer):
        raise NotImplementedError

    def depth_variable(self, variable_obj):
        var_coordinates = self._parse_data_coordinates(variable_obj)
        nc = self.netcdf4_dataset()
        for var_coordinate in var_coordinates:
            var_obj = nc.variables[var_coordinate]
            if ((hasattr(var_obj, 'axis') and var_obj.axis.lower().strip() == 'z') or
                (hasattr(var_obj, 'positive') and var_obj.positive.lower().strip() in ['up', 'down'])
                ):
                depth_variable = var_coordinate
                break
            else:
                depth_variable = None
        return depth_variable
    
    def _parse_data_coordinates(self, variable_obj):
        var_dims = variable_obj.dimensions
        var_coordinates = variable_obj.coordinates.strip().split()
        if len(var_dims) < len(var_coordinates):
            c_idx = len(var_coordinates) - len(var_dims)
            filtered_var_coord = var_coordinates[c_idx:]
        else:
            filtered_var_coord = var_coordinates
        return filtered_var_coord
        
    def _spatial_data_subset(self, data, spatial_index):
        rows = spatial_index[0, :]
        columns = spatial_index[1, :]
        data_subset = data[rows, columns]
        return data_subset
    
    def depth_direction(self, layer):
        raise NotImplementedError

    def depths(self, layer):
        raise NotImplementedError

    def humanize(self):
        return "SGRID"
