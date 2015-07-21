# -*- coding: utf-8 -*-
import os
import time
import bisect
import shutil
import tempfile
import itertools
from math import sqrt
from datetime import datetime

import pytz

from pyugrid import UGrid
from pyaxiom.netcdf import EnhancedDataset
import numpy as np
import netCDF4

import pandas as pd

import matplotlib.tri as Tri

import rtree

from wms.models import Dataset, Layer, VirtualLayer
from wms.utils import DotDict, calc_lon_lat_padding, calc_safety_factor

from wms import data_handler
from wms import mpl_handler
from wms import gfi_handler
from wms import gmd_handler

from wms import logger


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

    def has_cache(self):
        return os.path.exists(self.topology_file)

    def make_rtree(self):
        p = rtree.index.Property()
        p.overwrite = True
        p.storage   = rtree.index.RT_Disk
        p.Dimension = 2

        nc = self.netcdf4_dataset()
        ug = UGrid.from_nc_dataset(nc=nc)

        class FastRtree(rtree.Rtree):
            def dumps(self, obj):
                try:
                    import cPickle
                    return cPickle.dumps(obj, -1)
                except ImportError:
                    super(FastRtree, self).dumps(obj)

        def rtree_faces_generator_function():
            for face_idx, node_list in enumerate(ug.faces):
                nodes = ug.nodes[node_list]
                xmin, ymin = np.min(nodes, 0)
                xmax, ymax = np.max(nodes, 0)
                yield (face_idx, (xmin, ymin, xmax, ymax), face_idx)
        logger.info("Building Faces Rtree Topology Cache for {0}".format(self.name))
        _, face_temp_file = tempfile.mkstemp(suffix='.face')
        start = time.time()
        FastRtree(face_temp_file,
                  rtree_faces_generator_function(),
                  properties=p,
                  overwrite=True,
                  interleaved=True)
        logger.info("Built Faces Rtree Topology Cache in {0} seconds.".format(time.time() - start))
        shutil.move('{}.dat'.format(face_temp_file), self.face_tree_data_file)
        shutil.move('{}.idx'.format(face_temp_file), self.face_tree_index_file)

        def rtree_nodes_generator_function():
            for node_index, (x, y) in enumerate(ug.nodes):
                yield (node_index, (x, y, x, y), node_index)
        logger.info("Building Nodes Rtree Topology Cache for {0}".format(self.name))
        _, node_temp_file = tempfile.mkstemp(suffix='.node')
        start = time.time()
        FastRtree(node_temp_file,
                  rtree_nodes_generator_function(),
                  properties=p,
                  overwrite=True,
                  interleaved=True)
        logger.info("Built Nodes Rtree Topology Cache in {0} seconds.".format(time.time() - start))
        shutil.move('{}.dat'.format(node_temp_file), self.node_tree_data_file)
        shutil.move('{}.idx'.format(node_temp_file), self.node_tree_index_file)

        nc.close()

    def update_cache(self, force=False):
        try:
            nc = self.netcdf4_dataset()
            ug = UGrid.from_nc_dataset(nc=nc)
            ug.save_as_netcdf(self.topology_file)

            if not os.path.exists(self.topology_file):
                logger.error("Failed to create topology_file cache for Dataset '{}'".format(self.dataset))
                return

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
            pass  # We could still be updating the cache file
        finally:
            if nc is not None:
                nc.close()

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    def minmax(self, layer, request):
        time_index, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']

        try:
            nc = self.netcdf4_dataset()
            data_obj = nc.variables[layer.access_name]
            data_location = data_obj.location
            mesh_name = data_obj.mesh

            ug = UGrid.from_ncfile(self.topology_file, mesh_name=mesh_name)
            coords = np.empty(0)
            if data_location == 'node':
                coords = ug.nodes
            elif data_location == 'face':
                coords = ug.face_coordinates
            elif data_location == 'edge':
                coords = ug.edge_coordinates

            lon = coords[:, 0]
            lat = coords[:, 1]
            spatial_idx = data_handler.lat_lon_subset_idx(lon, lat, wgs84_bbox.minx, wgs84_bbox.miny, wgs84_bbox.maxx, wgs84_bbox.maxy)

            vmin = None
            vmax = None
            data = None
            if isinstance(layer, Layer):
                if (len(data_obj.shape) == 3):
                    z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                    data = data_obj[time_index, z_index, spatial_idx]
                elif (len(data_obj.shape) == 2):
                    data = data_obj[time_index, spatial_idx]
                elif len(data_obj.shape) == 1:
                    data = data_obj[spatial_idx]
                else:
                    logger.debug("Dimension Mismatch: data_obj.shape == {0} and time = {1}".format(data_obj.shape, time_value))

                if data is not None:
                    vmin = np.nanmin(data).item()
                    vmax = np.nanmax(data).item()
            elif isinstance(layer, VirtualLayer):

                # Data needs to be [var1,var2] where var are 1D (nodes only, elevation and time already handled)
                data = []
                for l in layer.layers:
                    data_obj = nc.variables[l.var_name]
                    if (len(data_obj.shape) == 3):
                        z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                        data.append(data_obj[time_index, z_index, spatial_idx])
                    elif (len(data_obj.shape) == 2):
                        data.append(data_obj[time_index, spatial_idx])
                    elif len(data_obj.shape) == 1:
                        data.append(data_obj[spatial_idx])
                    else:
                        logger.debug("Dimension Mismatch: data_obj.shape == {0} and time = {1}".format(data_obj.shape, time_value))

                if ',' in layer.var_name and data:
                    # Vectors, so return magnitude
                    data = [ sqrt((u*u) + (v*v)) for (u, v,) in data.T if u != np.nan and v != np.nan]
                    vmin = min(data)
                    vmax = max(data)

            return gmd_handler.from_dict(dict(min=vmin, max=vmax))

        finally:
            nc.close()

    def getmap(self, layer, request):
        time_index, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']

        try:
            nc = self.netcdf4_dataset()
            data_obj = nc.variables[layer.access_name]
            data_location = data_obj.location
            mesh_name = data_obj.mesh

            ug = UGrid.from_ncfile(self.topology_file, mesh_name=mesh_name)
            coords = np.empty(0)
            if data_location == 'node':
                coords = ug.nodes
            elif data_location == 'face':
                coords = ug.face_coordinates
            elif data_location == 'edge':
                coords = ug.edge_coordinates

            lon = coords[:, 0]
            lat = coords[:, 1]
            
            if request.GET['vectorscale']:  # is not None if vectors are being plotted
                vectorscale = request.GET['vectorscale']
                padding_factor = calc_safety_factor(vectorscale)
                spatial_idx_padding = calc_lon_lat_padding(lon, lat, padding_factor)
                spatial_idx = data_handler.lat_lon_subset_idx(lon, lat,
                                                              wgs84_bbox.minx,
                                                              wgs84_bbox.miny,
                                                              wgs84_bbox.maxx,
                                                              wgs84_bbox.maxy,
                                                              padding=spatial_idx_padding
                                                              )
            else:
                spatial_idx = data_handler.lat_lon_subset_idx(lon,lat,
                                                              wgs84_bbox.minx,
                                                              wgs84_bbox.miny,
                                                              wgs84_bbox.maxx,
                                                              wgs84_bbox.maxy
                                                              )

            face_indicies = ug.faces[:]
            face_indicies_spatial_idx = data_handler.faces_subset_idx(face_indicies, spatial_idx)

            # If no triangles intersect the field of view, return a transparent tile
            if (len(spatial_idx) == 0) or (len(face_indicies_spatial_idx) == 0):
                logger.debug("No triangles in field of view, returning empty tile.")
                return self.empty_response(layer, request)

            tri_subset = Tri.Triangulation(lon, lat, triangles=face_indicies[face_indicies_spatial_idx])

            if isinstance(layer, Layer):
                if (len(data_obj.shape) == 3):
                    z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                    data = data_obj[time_index, z_index, :]
                elif (len(data_obj.shape) == 2):
                    data = data_obj[time_index, :]
                elif len(data_obj.shape) == 1:
                    data = data_obj[:]
                else:
                    logger.debug("Dimension Mismatch: data_obj.shape == {0} and time = {1}".format(data_obj.shape, time_value))
                    return self.empty_response(layer, request)

                if request.GET['image_type'] == 'filledcontours':
                    return mpl_handler.tricontourf_response(tri_subset, data, request)
                else:
                    raise NotImplementedError('Image type "{}" is not supported.'.format(request.GET['image_type']))

            elif isinstance(layer, VirtualLayer):

                # Data needs to be [var1,var2] where var are 1D (nodes only, elevation and time already handled)
                data = []
                for l in layer.layers:
                    data_obj = nc.variables[l.var_name]
                    if (len(data_obj.shape) == 3):
                        z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                        data.append(data_obj[time_index, z_index, :])
                    elif (len(data_obj.shape) == 2):
                        data.append(data_obj[time_index, :])
                    elif len(data_obj.shape) == 1:
                        data.append(data_obj[:])
                    else:
                        logger.debug("Dimension Mismatch: data_obj.shape == {0} and time = {1}".format(data_obj.shape, time_value))
                        return self.empty_response(layer, request)

                if request.GET['image_type'] == 'vectors':
                    return mpl_handler.quiver_response(lon[spatial_idx],
                                                       lat[spatial_idx],
                                                       data[0][spatial_idx],
                                                       data[1][spatial_idx],
                                                       request,
                                                       vectorscale
                                                       )
                else:
                    raise NotImplementedError('Image type "{}" is not supported.'.format(request.GET['image_type']))
        finally:
            nc.close()

    def getfeatureinfo(self, layer, request):
        try:
            nc = self.netcdf4_dataset()
            topo = self.topology_dataset()
            data_obj = nc.variables[layer.access_name]
            data_location = data_obj.location
            # mesh_name = data_obj.mesh
            # Use local topology for pulling bounds data
            # ug = UGrid.from_ncfile(self.topology_file, mesh_name=mesh_name)

            geo_index, closest_x, closest_y, start_time_index, end_time_index, return_dates = self.setup_getfeatureinfo(topo, data_obj, request, location=data_location)

            logger.info("Start index: {}".format(start_time_index))
            logger.info("End index: {}".format(end_time_index))
            logger.info("Geo index: {}".format(geo_index))

            return_arrays = []
            z_value = None
            if isinstance(layer, Layer):
                if len(data_obj.shape) == 3:
                    z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                    data = data_obj[start_time_index:end_time_index, z_index, geo_index]
                elif len(data_obj.shape) == 2:
                    data = data_obj[start_time_index:end_time_index, geo_index]
                elif len(data_obj.shape) == 1:
                    data = data_obj[geo_index]
                else:
                    raise ValueError("Dimension Mismatch: data_obj.shape == {0} and time indexes = {1} to {2}".format(data_obj.shape, start_time_index, end_time_index))

                return_arrays.append((layer.var_name, data))

            elif isinstance(layer, VirtualLayer):

                # Data needs to be [var1,var2] where var are 1D (nodes only, elevation and time already handled)
                for l in layer.layers:
                    data_obj = nc.variables[l.var_name]
                    if len(data_obj.shape) == 3:
                        z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                        data.append(data_obj[start_time_index:end_time_index, z_index, geo_index])
                    elif len(data_obj.shape) == 2:
                        data.append(data_obj[start_time_index:end_time_index, geo_index])
                    elif len(data_obj.shape) == 1:
                        data.append(data_obj[geo_index])
                    else:
                        raise ValueError("Dimension Mismatch: data_obj.shape == {0} and time indexes = {1} to {2}".format(data_obj.shape, start_time_index, end_time_index))

                    return_arrays.append((l.var_name, data))

            # Data is now in the return_arrays list, as a list of numpy arrays.  We need
            # to add time and depth to them to create a single Pandas DataFrame
            if (len(data_obj.shape) == 3):
                df = pd.DataFrame({'time': return_dates,
                                   'x': closest_x,
                                   'y': closest_y,
                                   'z': z_value})
            elif (len(data_obj.shape) == 2):
                df = pd.DataFrame({'time': return_dates,
                                   'x': closest_x,
                                   'y': closest_y})
            elif (len(data_obj.shape) == 1):
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
            raise
        finally:
            nc.close()
            topo.close()

    def wgs84_bounds(self, layer):
        try:
            nc = self.netcdf4_dataset()
            data_location = nc.variables[layer.access_name].location
            mesh_name = nc.variables[layer.access_name].mesh
            # Use local topology for pulling bounds data
            ug = UGrid.from_ncfile(self.topology_file, mesh_name=mesh_name)
            coords = np.empty(0)
            if data_location == 'node':
                coords = ug.nodes
            elif data_location == 'face':
                coords = ug.face_coordinates
            elif data_location == 'edge':
                coords = ug.edge_coordinates

            minx = np.nanmin(coords[:, 1])
            miny = np.nanmin(coords[:, 0])
            maxx = np.nanmax(coords[:, 1])
            maxy = np.nanmax(coords[:, 0])

            return DotDict(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
        except AttributeError:
            pass
        finally:
            nc.close()

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
            return netCDF4.num2date(time_var[:], units=time_var.units)
        finally:
            nc.close()

    def depth_variable(self, layer):
        try:
            nc = self.netcdf4_dataset()
            layer_var = nc.variables[layer.access_name]
            for cv in layer_var.coordinates.strip().split():
                try:
                    coord_var = nc.variables[cv]
                    if hasattr(coord_var, 'axis') and coord_var.axis.lower().strip() == 'z':
                        return cv
                    elif hasattr(coord_var, 'positive') and coord_var.positive.lower().strip() in ['up', 'down']:
                        return cv
                except BaseException:
                    pass
        except AttributeError:
            pass
        finally:
            nc.close()

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
        d = self.depth_variable(layer)
        if d is not None:
            try:
                nc = self.netcdf4_dataset()
                return range(0, d.shape[0])
            finally:
                nc.close()
        return []

    def humanize(self):
        return "UGRID"
