# -*- coding: utf-8 -*-
from datetime import datetime
import bisect
import itertools
import os

import netCDF4 as nc4
import pyproj
import pytz
from pyaxiom.netcdf import EnhancedDataset
from pysgrid import from_nc_dataset, from_ncfile
from pysgrid.custom_exceptions import SGridNonCompliantError
from pysgrid.read_netcdf import NetCDFDataset
from pysgrid.processing_2d import avg_to_cell_center, rotate_vectors

from wms import mpl_handler
from wms.data_handler import lat_lon_subset_idx
from wms.models import Dataset, Layer, VirtualLayer


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

    def has_cache(self):
        return os.path.exists(self.topology_file)

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
        
    def _variable_data_trimming(self, variable, cached_variable, time_index, request):
        variable_dim_length = len(cached_variable.dimensions)
        if variable_dim_length >= 3:
            z = request.GET['elevation']
            vertical_idx = self.nearest_z(cached_variable.variable, z)[0]
            trimmed_variable = variable[time_index, vertical_idx, cached_variable.center_slicing[-2], cached_variable.center_slicing[-1]]
        elif variable_dim_length == 2:
            trimmed_variable = variable[time_index, cached_variable.center_slicing[-2], cached_variable.center_slicing[-3]]
        elif variable_dim_length == 1:
            trimmed_variable = variable[cached_variable.center_slicing]
        else:
            raise Exception('Unable to trim variable {0} data.'.format(cached_variable.variable))
        return trimmed_variable
        
    def getmap(self, layer, request):
        time_index = self.nearest_time(layer, request.GET['time'])[0]
        epsg_4326 = pyproj.Proj(init='EPSG:4326')
        bbox = request.GET['bbox']
        requested_crs = request.GET['crs']
        wgs84_minx, wgs84_miny = pyproj.transform(requested_crs, epsg_4326, bbox.minx, bbox.miny)
        wgs84_maxx, wgs84_maxy = pyproj.transform(requested_crs, epsg_4326, bbox.maxx, bbox.maxy)
        nc = self.netcdf4_dataset()
        cached_sg = from_ncfile(self.topology_file)
        lon_name, lat_name = cached_sg.face_coordinates
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
        lyr_access_name = layer.var_name
        split_lyr_vars = lyr_access_name.split(',')
        lyr_vars = {}
        for var_idx, var_name in enumerate(split_lyr_vars):
            lv_key = 'var{0}'.format(var_idx)
            lyr_vars[lv_key] = var_name
        # let's just handle instances of 1 or 2 variables for now
        # a request of 2 variables will be a request for a virtual layer
        # i think if 2 variables are requested, they would probably be defined on the grid
        grid_variables = cached_sg.grid_variables
        if len(lyr_vars) == 2 and set(split_lyr_vars).issubset(grid_variables):
            var0_name = lyr_vars['var0']
            var1_name = lyr_vars['var1']
            var0_obj = getattr(cached_sg, var0_name)
            var1_obj = getattr(cached_sg, var1_name)
            raw_var0 = nc.variables[var0_name]
            raw_var1 = nc.variables[var1_name]
            if len(var0_obj.dimensions) == len(var1_obj.dimensions):
                var0_data_trimmed = self._variable_data_trimming(raw_var0, var0_obj, time_index, request)
                var1_data_trimmed = self._variable_data_trimming(raw_var1, var1_obj, time_index, request)
            else:
                raise AttributeError('One or both of the specified variables has screwed up dimensions.')
            var0_avg = avg_to_cell_center(var0_data_trimmed, var0_obj.center_axis)
            var1_avg = avg_to_cell_center(var1_data_trimmed, var1_obj.center_axis)
            if var0_obj.vector_axis is not None and var1_obj is not None:
                if var0_obj.vector_axis.lower() == 'x' and var1_obj.vector_axis.lower() == 'y':
                    x_var = var0_avg
                    y_var = var1_avg
                elif var0_obj.vector_axis.lower() == 'y' and var1_obj.vector_axis.lower() == 'x':
                    x_var = var1_avg
                    y_var = var0_avg
            # if unable to determine from vector_axis attribute, try center_axis
            # this is less reliable....
            else:
                if var0_obj.center_axis == 1 and var1_obj.center_axis == 0:
                    x_var = var0_avg
                    y_var = var1_avg
                elif var0_obj.center_axis == 0 and var1_obj.center_axis == 1:
                    x_var = var1_avg
                    y_var = var0_avg
                else:
                    raise Exception('Unable to determine x and y variables.')
            # rotate vectors
            angles = cached_sg.angles[lon_obj.center_slicing]
            x_rot, y_rot = rotate_vectors(x_var, y_var, angles)
            spatial_subset_x_rot = self._spatial_data_subset(x_rot, spatial_idx)
            spatial_subset_y_rot = self._spatial_data_subset(y_rot, spatial_idx)
        # deal with requests for a single variable
        elif len(lyr_vars) == 1:
            var0_name = lyr_vars['var0']
            var0_obj = getattr(cached_sg, var0_name)
            raw_var0 = nc.variables[var0_name]
            var0_data_trimmed = self._variable_data_trimming(raw_var0, var0_obj, time_index, request)
            # handle grid variables
            if set(lyr_vars).issubset(grid_variables):
                var0_cell_center_data = avg_to_cell_center(var0_data_trimmed, var0_obj.center_axis)
            # handle non-grid variables
            else:
                var0_cell_center_data = var0_data_trimmed
        else:
            msg = ('Only layers with 1 or 2 variables are currently supported. ' 
                   'The request layer contains {0} layers.').format(len(lyr_vars))
            raise ValueError(msg)
        # deal with rendering a map image
        if isinstance(layer, Layer):
            if var0_obj.center_axis is None:
                colormesh_resp = mpl_handler.pcolormesh_response(lon,
                                                                 lat,
                                                                 data=var0_cell_center_data, 
                                                                 request=request
                                                                 )
                return colormesh_resp
            else:
                pass
        elif isinstance(layer, VirtualLayer):
            if request.GET['image_type'] == 'vectors':
                if len(lyr_vars) == 2:
                    quiver_resp = mpl_handler.quiver_response(subset_lon,
                                                              subset_lat,
                                                              spatial_subset_x_rot,
                                                              spatial_subset_y_rot,
                                                              request
                                                              )
                    return quiver_resp
        
    
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
    
    def nearest_z(self, layer_access_name, z):
        """
        Return the z index and z value that is closest
        
        """
        depths = self.depths(layer_access_name)
        depth_idx = bisect.bisect_right(depths, z)
        try:
            depth = depths[depth_idx]
        except IndexError:
            depth_idx -= 1
            depth = depth[depth_idx]
        return depth_idx, depth
        
    def times(self, layer):
        raise NotImplementedError

    def depth_variable(self, layer_access_name):
        var_coordinates = self._parse_data_coordinates(layer_access_name)
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
    
    def _parse_data_coordinates(self, layer_access_name):
        variable_obj = self.netcdf4_dataset().variables[layer_access_name]
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

    def depths(self, layer_access_name):
        depth_variable = self.depth_variable(layer_access_name)
        depth_data = self.netcdf4_dataset().variables[depth_variable][:]
        return depth_data

    def humanize(self):
        return "SGRID"
