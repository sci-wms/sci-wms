# -*- coding: utf-8 -*-
import os
import time
import shutil
from datetime import datetime
import bisect
import tempfile
import itertools

import numpy as np
import netCDF4 as nc4
import pyproj
import pytz
from pyaxiom.netcdf import EnhancedDataset
from pysgrid import from_nc_dataset, from_ncfile
from pysgrid.custom_exceptions import SGridNonCompliantError
from pysgrid.read_netcdf import NetCDFDataset
from pysgrid.processing_2d import avg_to_cell_center, rotate_vectors

import pandas as pd

import rtree

from wms import mpl_handler
from wms import gfi_handler
from wms import data_handler
from wms import views
from wms.models import Dataset, Layer, VirtualLayer
from wms.utils import DotDict, calc_lon_lat_padding, calc_safety_factor

from wms import logger


class SGridDataset(Dataset):

    @staticmethod
    def is_valid(uri):
        ds = None
        try:
            ds = EnhancedDataset(uri)
            nc_ds = NetCDFDataset(ds)
        except (AttributeError, RuntimeError, SGridNonCompliantError):
            return False
        else:
            if nc_ds.sgrid_compliant_file() or 'SGRID' in ds.conventions:
                return True
            else:
                return False
        finally:
            if ds is not None:
                ds.close()

    def has_cache(self):
        return os.path.exists(self.topology_file)

    def make_rtree(self):
        p = rtree.index.Property()
        p.overwrite = True
        p.storage   = rtree.index.RT_Disk
        p.Dimension = 2

        nc = self.netcdf4_dataset()
        sg = from_nc_dataset(nc)

        class FastRtree(rtree.Rtree):
            def dumps(self, obj):
                try:
                    import cPickle
                    return cPickle.dumps(obj, -1)
                except ImportError:
                    super(FastRtree, self).dumps(obj)

        def rtree_generator_function():
            for i, axis in enumerate(sg.centers):
                for j, (x, y) in enumerate(axis):
                    yield (i+j, (x, y, x, y), (i, j))

        logger.info("Building Faces (centers) Rtree Topology Cache for {0}".format(self.name))
        _, temp_file = tempfile.mkstemp(suffix='.face')
        start = time.time()
        FastRtree(temp_file,
                  rtree_generator_function(),
                  properties=p,
                  overwrite=True,
                  interleaved=True)
        logger.info("Built Faces (centers) Rtree Topology Cache in {0} seconds.".format(time.time() - start))

        shutil.move('{}.dat'.format(temp_file), self.face_tree_data_file)
        shutil.move('{}.idx'.format(temp_file), self.face_tree_index_file)

        nc.close()

    def update_cache(self, force=False):
        try:
            nc = self.netcdf4_dataset()
            sg = from_nc_dataset(nc)
            sg.save_as_netcdf(self.topology_file)

            if not os.path.exists(self.topology_file):
                logger.error("Failed to create topology_file cache for Dataset '{}'".format(self.dataset))
                return

            # add time to the cached topology
            time_vars = nc.get_variables_by_attributes(standard_name='time')
            time_dims = list(itertools.chain.from_iterable([time_var.dimensions for time_var in time_vars]))
            unique_time_dims = list(set(time_dims))
            with EnhancedDataset(self.topology_file, mode='a') as cached_nc:
                # create pertinent time dimensions if they aren't already present
                for unique_time_dim in unique_time_dims:
                    dim_size = len(nc.dimensions[unique_time_dim])
                    try:
                        cached_nc.createDimension(unique_time_dim, size=dim_size)
                    except RuntimeError:
                        continue
                # support cases where there may be more than one variable with standard_name='time' in a dataset
                for time_var in time_vars:
                    try:
                        time_var_obj = cached_nc.createVariable(time_var.name,
                                                                time_var.dtype,
                                                                time_var.dimensions)
                    except RuntimeError:
                        time_var_obj = cached_nc.variables[time_var.name]
                    finally:
                        time_var_obj[:] = time_var[:]
                        time_var_obj.units = time_var.units
                        time_var_obj.standard_name = 'time'

            # Now do the RTree index
            self.make_rtree()

        except RuntimeError:
            pass  # Could still be updating (write-lock)
        finally:
            if nc is not None:
                nc.close()

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    def getmap(self, layer, request):
        time_index, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']

        try:
            nc = self.canon_dataset
            cached_sg = from_ncfile(self.topology_file)
            lon_name, lat_name = cached_sg.face_coordinates
            lon_obj = getattr(cached_sg, lon_name)
            lat_obj = getattr(cached_sg, lat_name)
            centers = cached_sg.centers
            lon = centers[..., 0][lon_obj.center_slicing]
            lat = centers[..., 1][lat_obj.center_slicing]
            grid_variables = cached_sg.grid_variables

            if isinstance(layer, Layer):
                data_obj = getattr(cached_sg, layer.access_name)
                raw_var = nc.variables[layer.access_name]
                if len(raw_var.shape) >= 3:
                    z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                    raw_data = raw_var[time_index, z_index, data_obj.center_slicing[-2], data_obj.center_slicing[-1]]
                elif len(raw_var.shape) == 2:
                    raw_data = raw_var[time_index, data_obj.center_slicing[-2], data_obj.center_slicing[-3]]
                elif len(raw_var.shape) == 1:
                    raw_data = raw_var[data_obj.center_slicing]
                else:
                    raise BaseException('Unable to trim variable {0} data.'.format(layer.access_name))
                # handle grid variables
                if set([layer.access_name]).issubset(grid_variables):
                    raw_data = avg_to_cell_center(raw_data, data_obj.center_axis)

                if request.GET['image_type'] == 'pcolor':
                    return mpl_handler.pcolormesh_response(lon, lat, data=raw_data, request=request)
                elif request.GET['image_type'] == 'filledcontours':
                    return mpl_handler.contourf_response(lon, lat, data=raw_data, request=request)
                else:
                    raise NotImplementedError('Image type "{}" is not supported.'.format(request.GET['image_type']))

            elif isinstance(layer, VirtualLayer):
                x_var = None
                y_var = None
                raw_vars = []
                for l in layer.layers:
                    data_obj = getattr(cached_sg, l.access_name)
                    raw_var = nc.variables[l.access_name]
                    raw_vars.append(raw_var)
                    if len(raw_var.shape) == 4:
                        z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                        raw_data = raw_var[time_index, z_index, data_obj.center_slicing[-2], data_obj.center_slicing[-1]]
                    elif len(raw_var.shape) == 3:
                        raw_data = raw_var[time_index, data_obj.center_slicing[-2], data_obj.center_slicing[-3]]
                    elif len(raw_var.shape) == 2:
                        raw_data = raw_var[data_obj.center_slicing]
                    else:
                        raise BaseException('Unable to trim variable {0} data.'.format(l.access_name))

                    raw_data = avg_to_cell_center(raw_data, data_obj.center_axis)
                    if x_var is None:
                        if data_obj.vector_axis and data_obj.vector_axis.lower() == 'x':
                            x_var = raw_data
                        elif data_obj.center_axis == 1:
                            x_var = raw_data

                    if y_var is None:
                        if data_obj.vector_axis and data_obj.vector_axis.lower() == 'y':
                            y_var = raw_data
                        elif data_obj.center_axis == 0:
                            y_var = raw_data

                if x_var is None or y_var is None:
                    raise BaseException('Unable to determine x and y variables.')

                dim_lengths = [ len(v.dimensions) for v in raw_vars ]
                if len(list(set(dim_lengths))) != 1:
                    raise AttributeError('One or both of the specified variables has screwed up dimensions.')

                if request.GET['image_type'] == 'vectors':
                    vectorscale = request.GET['vectorscale']
                    padding_factor = calc_safety_factor(vectorscale)
                    spatial_idx_padding = calc_lon_lat_padding(lon, lat, padding_factor)
                    spatial_idx = data_handler.lat_lon_subset_idx(lon, lat,
                                                                  lonmin=wgs84_bbox.minx,
                                                                  latmin=wgs84_bbox.miny,
                                                                  lonmax=wgs84_bbox.maxx,
                                                                  latmax=wgs84_bbox.maxy,
                                                                  padding=spatial_idx_padding
                                                                  )
                    subset_lon = self._spatial_data_subset(lon, spatial_idx)
                    subset_lat = self._spatial_data_subset(lat, spatial_idx)
                    # rotate vectors
                    angles = cached_sg.angles[lon_obj.center_slicing]
                    x_rot, y_rot = rotate_vectors(x_var, y_var, angles)
                    spatial_subset_x_rot = self._spatial_data_subset(x_rot, spatial_idx)
                    spatial_subset_y_rot = self._spatial_data_subset(y_rot, spatial_idx)
                    return mpl_handler.quiver_response(subset_lon,
                                                       subset_lat,
                                                       spatial_subset_x_rot,
                                                       spatial_subset_y_rot,
                                                       request,
                                                       vectorscale
                                                       )
                else:
                    raise NotImplementedError('Image type "{}" is not supported.'.format(request.GET['image_type']))
        except BaseException:
            logger.exception("Could not process GetFeatureInfo request")
            raise
        finally:
            nc.close()

    def getfeatureinfo(self, layer, request):
        try:
            nc = self.netcdf4_dataset()
            topo = self.topology_dataset()
            data_obj = nc.variables[layer.access_name]

            geo_index, closest_x, closest_y, start_time_index, end_time_index, return_dates = self.setup_getfeatureinfo(topo, data_obj, request)

            return_arrays = []
            z_value = None
            if isinstance(layer, Layer):
                if len(data_obj.shape) == 4:
                    z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                    data = data_obj[start_time_index:end_time_index, z_index, geo_index[0], geo_index[1]]
                elif len(data_obj.shape) == 3:
                    data = data_obj[start_time_index:end_time_index, geo_index[0], geo_index[1]]
                elif len(data_obj.shape) == 2:
                    data = data_obj[geo_index[0], geo_index[1]]
                else:
                    raise ValueError("Dimension Mismatch: data_obj.shape == {0} and time indexes = {1} to {2}".format(data_obj.shape, start_time_index, end_time_index))

                return_arrays.append((layer.var_name, data))

            elif isinstance(layer, VirtualLayer):

                # Data needs to be [var1,var2] where var are 1D (nodes only, elevation and time already handled)
                for l in layer.layers:
                    if len(data_obj.shape) == 4:
                        z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                        data = data_obj[start_time_index:end_time_index, z_index, geo_index[0], geo_index[1]]
                    elif len(data_obj.shape) == 3:
                        data = data_obj[start_time_index:end_time_index, geo_index[0], geo_index[1]]
                    elif len(data_obj.shape) == 2:
                        data = data_obj[geo_index[0], geo_index[1]]
                    else:
                        raise ValueError("Dimension Mismatch: data_obj.shape == {0} and time indexes = {1} to {2}".format(data_obj.shape, start_time_index, end_time_index))
                    return_arrays.append((l.var_name, data))

            # Data is now in the return_arrays list, as a list of numpy arrays.  We need
            # to add time and depth to them to create a single Pandas DataFrame
            if len(data_obj.shape) == 4:
                df = pd.DataFrame({'time': return_dates,
                                   'x': closest_x,
                                   'y': closest_y,
                                   'z': z_value})
            elif len(data_obj.shape) == 3:
                df = pd.DataFrame({'time': return_dates,
                                   'x': closest_x,
                                   'y': closest_y})
            elif len(data_obj.shape) == 2:
                df = pd.DataFrame({'x': closest_x,
                                   'y': closest_y})
            else:
                df = pd.DataFrame()

            # Now add a column for each member of the return_arrays list
            for (var_name, np_array) in return_arrays:
                df.loc[:, var_name] = pd.Series(np_array, index=df.index)

            return gfi_handler.from_dataframe(request, df)

        except BaseException:
            logger.exception("Could not process GetFeatureInfo request")
        finally:
            nc.close()
            topo.close()

    def wgs84_bounds(self, layer):
        try:
            cached_sg = from_ncfile(self.topology_file)
        except:
            pass
        else:
            centers = cached_sg.centers
            longitudes = centers[..., 0]
            latitudes = centers[..., 1]
            lon_name, lat_name = cached_sg.face_coordinates
            lon_var_obj = getattr(cached_sg, lon_name)
            lat_var_obj = getattr(cached_sg, lat_name)
            lon_trimmed = longitudes[lon_var_obj.center_slicing]
            lat_trimmed = latitudes[lat_var_obj.center_slicing]
            lon_max = lon_trimmed.max()
            lon_min = lon_trimmed.min()
            lat_max = lat_trimmed.max()
            lat_min = lat_trimmed.min()
            return DotDict(minx=lon_min,
                           miny=lat_min,
                           maxx=lon_max,
                           maxy=lat_max
                           )

    def nearest_z(self, layer, z):
        """
        Return the z index and z value that is closest
        """
        depths = self.depths(layer)
        depth_idx = bisect.bisect_right(depths, z)
        try:
            depths[depth_idx]
        except IndexError:
            depth_idx -= 1
        return depth_idx, depths[depth_idx]

    def times(self, layer):
        try:
            nc = self.topology_dataset()
            time_var = nc.get_variables_by_attributes(standard_name='time')[0]
            return nc4.num2date(time_var[:], units=time_var.units)
        finally:
            nc.close()

    def depth_variable(self, layer):
        try:
            nc = self.canon_dataset
            layer_var = nc.variables[layer.access_name]
            for cv in layer_var.coordinates.strip().split():
                try:
                    coord_var = nc.variables[cv]
                    if hasattr(coord_var, 'axis') and coord_var.axis.lower().strip() == 'z':
                        return coord_var
                    elif hasattr(coord_var, 'positive') and coord_var.positive.lower().strip() in ['up', 'down']:
                        return coord_var
                except BaseException:
                    pass
        except AttributeError:
            pass
        finally:
            nc.close()

    def _spatial_data_subset(self, data, spatial_index):
        rows = spatial_index[0, :]
        columns = spatial_index[1, :]
        data_subset = data[rows, columns]
        return data_subset

    # same as ugrid
    def depth_direction(self, layer):
        d = self.depth_variable(layer)
        if d is not None:
            try:
                nc = self.netcdf4_dataset()
                if hasattr(d, 'positive'):
                    return d.positive
            finally:
                nc.close()
        return 'unknown'

    def depths(self, layer):
        """ sci-wms only deals in depth indexes at this time (no sigma) """
        d = self.depth_variable(layer)
        if d is not None:
            return range(0, d.shape[0])
        return []

    def humanize(self):
        return "SGRID"
