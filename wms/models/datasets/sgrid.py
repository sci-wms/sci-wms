# -*- coding: utf-8 -*-
import os
import time
import shutil
from datetime import datetime
import bisect
import tempfile
import itertools
from math import sqrt
import warnings

import numpy as np
import numpy.ma as ma
import netCDF4 as nc4
import pytz
from pyaxiom.netcdf import EnhancedDataset, EnhancedMFDataset
from pysgrid import from_nc_dataset, from_ncfile
from pysgrid.custom_exceptions import SGridNonCompliantError
from pysgrid.read_netcdf import NetCDFDataset as SGrid
from pysgrid.processing_2d import avg_to_cell_center, rotate_vectors

import pandas as pd

import rtree

from wms import mpl_handler
from wms import gfi_handler
from wms import data_handler
from wms import gmd_handler


from wms.models import Dataset, Layer, VirtualLayer, NetCDFDataset
from wms.utils import DotDict, calc_lon_lat_padding, calc_safety_factor, find_appropriate_time


from wms import logger


class SGridDataset(Dataset, NetCDFDataset):

    @staticmethod
    def is_valid(uri):
        try:
            with EnhancedDataset(uri) as ds:
                nc_ds = SGrid(ds)
                return nc_ds.sgrid_compliant_file() or 'sgrid' in ds.Conventions.lower()
        except RuntimeError:
            try:
                with EnhancedMFDataset(uri, aggdim='time') as ds:
                    nc_ds = SGrid(ds)
                    return nc_ds.sgrid_compliant_file() or 'sgrid' in ds.Conventions.lower()
            except (AttributeError, RuntimeError, SGridNonCompliantError):
                return False
        except (AttributeError, SGridNonCompliantError):
            return False

    def has_cache(self):
        return os.path.exists(self.topology_file)

    def make_rtree(self):
        p = rtree.index.Property()
        p.overwrite = True
        p.storage   = rtree.index.RT_Disk
        p.Dimension = 2

        with self.dataset() as nc:
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

    def update_cache(self, force=False):
        with self.dataset() as nc:
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

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    def minmax(self, layer, request):
        time_index, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']

        with self.dataset() as nc:
            cached_sg = from_ncfile(self.topology_file)
            lon_name, lat_name = cached_sg.face_coordinates
            lon_obj = getattr(cached_sg, lon_name)
            lat_obj = getattr(cached_sg, lat_name)
            centers = cached_sg.centers
            lon = centers[..., 0][lon_obj.center_slicing]
            lat = centers[..., 1][lat_obj.center_slicing]
            spatial_idx = data_handler.lat_lon_subset_idx(lon, lat,
                                                          lonmin=wgs84_bbox.minx,
                                                          latmin=wgs84_bbox.miny,
                                                          lonmax=wgs84_bbox.maxx,
                                                          latmax=wgs84_bbox.maxy
                                                          )
            subset_lon = np.unique(spatial_idx[0])
            subset_lat = np.unique(spatial_idx[1])
            grid_variables = cached_sg.grid_variables

            vmin = None
            vmax = None
            raw_data = None
            if isinstance(layer, Layer):
                data_obj = getattr(cached_sg, layer.access_name)
                raw_var = nc.variables[layer.access_name]
                if len(raw_var.shape) == 4:
                    z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                    raw_data = raw_var[time_index, z_index, subset_lon, subset_lat]
                elif len(raw_var.shape) == 3:
                    raw_data = raw_var[time_index, subset_lon, subset_lat]
                elif len(raw_var.shape) == 2:
                    raw_data = raw_var[subset_lon, subset_lat]
                else:
                    raise BaseException('Unable to trim variable {0} data.'.format(layer.access_name))

                # handle grid variables
                if set([layer.access_name]).issubset(grid_variables):
                    raw_data = avg_to_cell_center(raw_data, data_obj.center_axis)

                vmin = np.nanmin(raw_data).item()
                vmax = np.nanmax(raw_data).item()

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
                        raw_data = raw_var[time_index, z_index, subset_lon, subset_lat]
                    elif len(raw_var.shape) == 3:
                        raw_data = raw_var[time_index, subset_lon, subset_lat]
                    elif len(raw_var.shape) == 2:
                        raw_data = raw_var[subset_lon, subset_lat]
                    else:
                        raise BaseException('Unable to trim variable {0} data.'.format(l.access_name))

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

                if ',' in layer.var_name and raw_data is not None:
                    # Vectors, so return magnitude
                    data = [ sqrt((u*u) + (v*v)) for (u, v,) in zip(x_var.flatten(), y_var.flatten()) if u != np.nan and v != np.nan]
                    vmin = min(data)
                    vmax = max(data)

            return gmd_handler.from_dict(dict(min=vmin, max=vmax))

    def getmap(self, layer, request):
        time_index, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']

        with self.dataset() as nc:
            cached_sg = from_ncfile(self.topology_file)
            lon_name, lat_name = cached_sg.face_coordinates
            lon_obj = getattr(cached_sg, lon_name)
            lat_obj = getattr(cached_sg, lat_name)
            centers = cached_sg.centers
            lon = centers[..., 0][lon_obj.center_slicing]
            lat = centers[..., 1][lat_obj.center_slicing]
            if request.GET['image_type'] == 'vectors':
                vectorstep = request.GET['vectorstep']
                vectorscale = request.GET['vectorscale']
                padding_factor = calc_safety_factor(vectorscale)
                spatial_idx_padding = calc_lon_lat_padding(lon, lat, padding_factor)
            else:
                spatial_idx_padding = 0.18
                vectorstep = None
            spatial_idx = data_handler.lat_lon_subset_idx(lon, lat,
                                                          lonmin=wgs84_bbox.minx,
                                                          latmin=wgs84_bbox.miny,
                                                          lonmax=wgs84_bbox.maxx,
                                                          latmax=wgs84_bbox.maxy,
                                                          padding=spatial_idx_padding
                                                         )
            subset_x = np.unique(spatial_idx[0])
            subset_y = np.unique(spatial_idx[1])
            if subset_x.shape == (0, ) and subset_y.shape == (0, ):
                return mpl_handler.empty_response()  # return an empty tile if subset contains no data
            else:
                x_min_idx = subset_x.min()
                x_max_idx = subset_x.max() + 1
                y_min_idx = subset_y.min()
                y_max_idx = subset_y.max() + 1
                lonlat_mask = np.ones(lon.shape)
                lonlat_mask[spatial_idx[0], spatial_idx[1]] = 0
                trimmed_lon = ma.masked_array(lon, mask=lonlat_mask).data[x_min_idx:x_max_idx:vectorstep, y_min_idx:y_max_idx:vectorstep]
                trimmed_lat = ma.masked_array(lat, mask=lonlat_mask).data[x_min_idx:x_max_idx:vectorstep, y_min_idx:y_max_idx:vectorstep]
                if isinstance(layer, Layer):
                    data_obj = getattr(cached_sg, layer.access_name)
                    raw_var = nc.variables[layer.access_name]
                    raw_data = self._retrieve_data(request=request,
                                                   nc_variable=raw_var,
                                                   sg_variable=data_obj,
                                                   layer=layer,
                                                   subset_x=subset_x,
                                                   subset_y=subset_y,
                                                   time_index=time_index,
                                                   vectorstep=1
                                                   )
                    # handle edge variables
                    if data_obj.location is not None and 'edge' in data_obj.location:
                        raw_data = avg_to_cell_center(raw_data, data_obj.center_axis)
                    if request.GET['image_type'] == 'pcolor':
                        return mpl_handler.pcolormesh_response(trimmed_lon, trimmed_lat, data=raw_data, request=request)
                    elif request.GET['image_type'] == 'filledcontours':
                        return mpl_handler.contourf_response(trimmed_lon, trimmed_lat, data=raw_data, request=request)
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
                        raw_data = self._retrieve_data(request=request,
                                                       nc_variable=raw_var,
                                                       sg_variable=data_obj,
                                                       layer=layer,
                                                       subset_x=subset_x,
                                                       subset_y=subset_y,
                                                       time_index=time_index,
                                                       vectorstep=vectorstep
                                                       )
                        raw_data = self._avg_to_cell_center(raw_data, data_obj.center_axis, vectorstep)
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
                        angles = cached_sg.angles[lon_obj.center_slicing]
                        trimmed_angles = ma.masked_array(angles, mask=lonlat_mask).data[x_min_idx:x_max_idx:vectorstep, y_min_idx:y_max_idx:vectorstep]
                        # rotate vectors
                        x_rot, y_rot = rotate_vectors(x_var, y_var, trimmed_angles)
                        return mpl_handler.quiver_response(trimmed_lon,
                                                           trimmed_lat,
                                                           x_rot,
                                                           y_rot,
                                                           request,
                                                           vectorscale
                                                           )
                    else:
                        raise NotImplementedError('Image type "{}" is not supported.'.format(request.GET['image_type']))

    def getfeatureinfo(self, layer, request):
        with self.dataset() as nc:
            with self.topology() as topo:
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
        with self.topology() as nc:
            time_vars = nc.get_variables_by_attributes(standard_name='time')
            if len(time_vars) == 1:
                time_var = time_vars[0]
            else:
                # if there is more than variable with standard_name = time
                # fine the appropriate one to use with the layer
                var_obj = nc.variables[layer.access_name]
                time_var_name = find_appropriate_time(var_obj, time_vars)
                time_var = nc.variables[time_var_name]
            return nc4.num2date(time_var[:], units=time_var.units)

    def depth_variable(self, layer):
        with self.dataset() as nc:
            try:
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

    def _spatial_data_subset(self, data, spatial_index):
        rows = spatial_index[0, :]
        columns = spatial_index[1, :]
        data_subset = data[rows, columns]
        return data_subset
    
    def _avg_to_cell_center(self, data_array, avg_dim, vectorstep):
        """
        Given a two-dimensional numpy.array, average
        adjacent row values (avg_dim=1) or adjacent
        column values (avg_dim=0) to the grid cell
        center.
        
        :param data_array: 2-dimensional data
        :type data_array: numpy.array
        :param int avg_dim: integer specify array axis to be averaged
        :return: averages
        :rtype: numpy.array
        
        """
        if avg_dim == 0:
            da = np.transpose(data_array)
        else:
            da = data_array
        da_trim_low = da[:, 1:][::vectorstep, ::vectorstep]
        da_trim_high = da[:, :-1][::vectorstep, ::vectorstep]
        da_avg_raw = 0.5 * (da_trim_low + da_trim_high)
        if avg_dim == 0:
            da_avg = np.transpose(da_avg_raw)
        else:
            da_avg = da_avg_raw
        return da_avg
    
    def _vector_spatial_subset_adjustment(self, subset_x, subset_y, sg_variable, vectorstep=1):
        """
        Vectors are on the edges rather then face centers.
        Hence, using indices derived from face centered variables
        causes offset problems. This function adapts face centered
        indices to work with variables defined on an edge.
        
        Does not currently deal with indices on nodes.
        
        """
        # adjust for slicing and the index offset changes it causes
        subset_x, subset_y = self._adjust_subsets_for_slicing(subset_x, subset_y, sg_variable)
        # make sure there are enough values to do vector averaging correctly
        # expand the indices to cover large vector step
        # handle variables defined on the "x-axis"
        x_axis_def = ('x', 1)  # how "x" directed vectors can be identified
        y_axis_def = ('y', 0)  # how "y" directed vectors can be identified
        # handle variables defined on the "x-axis"
        new_subset_y = self._expand_vector_indices(subset_y, sg_variable, vectorstep, x_axis_def)
        # handle variables defined on the "y-axis"
        new_subset_x = self._expand_vector_indices(subset_x, sg_variable, vectorstep, y_axis_def)
        return new_subset_x, new_subset_y
    
    def _adjust_subsets_for_slicing(self, subset_x, subset_y, sg_variable):
        np_no_slice = np.s_[:]
        sliced_index = next((i for i, v in enumerate(sg_variable.center_slicing) if v != np_no_slice), None)
        if sliced_index is not None:
            x_axis = sg_variable.x_axis
            y_axis = sg_variable.y_axis
            try:
                x_dim_index = sg_variable.dimensions.index(x_axis)
            except ValueError:
                x_dim_index = None
            try:
                y_dim_index = sg_variable.dimensions.index(y_axis)
            except ValueError:
                y_dim_index = None
            slice_start = sg_variable.center_slicing[sliced_index].start
            if sliced_index == x_dim_index:  # slicing on x, adjust x
                subset_x = subset_x + slice_start
            if sliced_index == y_dim_index:  # slicing on y, adjust y:
                subset_y = subset_y + slice_start
            if x_dim_index is None and y_dim_index is None:
                # if axis attributes are missing
                # assume last var in dimension is "y"
                # assume second to last is "x"
                warning_msg = ('Unable to unambiguously determine variable slice axes. '
                               'Proceeding with assumption based on position.'
                               )
                warnings.warn(warning_msg,
                              RuntimeWarning
                              )
                if sg_variable.dimensions[sliced_index] == sg_variable.dimensions[-2]:
                    subset_x = subset_x + slice_start
                if sg_variable.dimensions[sliced_index] == sg_variable.dimensions[-1]:
                    subset_y = subset_y + slice_start
        return subset_x, subset_y
    
    def _expand_vector_indices(self, indices_subset, sg_variable, vectorstep, axis_def):
        axis, center_axis = axis_def
        subset_max = indices_subset.max()
        if ((sg_variable.vector_axis and sg_variable.vector_axis.lower() == axis) or
            (sg_variable.center_axis == center_axis)
            ):
            new_indices_subset = np.append(indices_subset, np.array(subset_max + 1, subset_max + 1*vectorstep))
        else:
            new_indices_subset = indices_subset
        return new_indices_subset
    
    def _spatial_subset_adjustment(self, subset_x, subset_y, sg_variable, vectorstep=1):
        if 'edge' in sg_variable.location:
            subset_x_mod, subset_y_mod = self._vector_spatial_subset_adjustment(subset_x,
                                                                                subset_y,
                                                                                sg_variable,
                                                                                vectorstep
                                                                                )
        else:
            subset_x_mod = subset_x
            subset_y_mod = subset_y
        return subset_x_mod, subset_y_mod
    
    def _retrieve_data(self,
                       request,
                       nc_variable,
                       sg_variable,
                       layer,
                       subset_x,
                       subset_y,
                       time_index,
                       vectorstep
                       ):
        subset_x_mod, subset_y_mod = self._spatial_subset_adjustment(subset_x,
                                                                     subset_y,
                                                                     sg_variable,
                                                                     vectorstep
                                                                     )
        if len(nc_variable.shape) == 4:
            z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
            raw_data = nc_variable[time_index, z_index, subset_x_mod, subset_y_mod]
        elif len(nc_variable.shape) == 3:
            raw_data = nc_variable[time_index, subset_x_mod, subset_y_mod]
        elif len(nc_variable.shape) == 2:
            raw_data = nc_variable[subset_x_mod, subset_y_mod]
        else:
            raise BaseException('Unable to trim variable {0} data.'.format(layer.access_name))
        return raw_data
    
    # same as ugrid
    def depth_direction(self, layer):
        d = self.depth_variable(layer)
        if d is not None:
            if hasattr(d, 'positive'):
                return d.positive
        return 'unknown'

    def depths(self, layer):
        """ sci-wms only deals in depth indexes at this time (no sigma) """
        d = self.depth_variable(layer)
        if d is not None:
            return range(0, d.shape[0])
        return []

    def humanize(self):
        return "SGRID"