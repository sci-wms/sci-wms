# -*- coding: utf-8 -*-
import os
import time
import bisect
import shutil
import tempfile
from math import sqrt

from pyugrid import UGrid
from pyaxiom.netcdf import EnhancedDataset, EnhancedMFDataset
import numpy as np
import netCDF4 as nc4

import pandas as pd

import matplotlib.tri as Tri

from rtree import index

from django.core.cache import caches

from wms import data_handler
from wms import mpl_handler
from wms import gfi_handler
from wms import gmd_handler

from wms.models import Dataset, Layer, VirtualLayer, NetCDFDataset
from wms.utils import DotDict, calc_lon_lat_padding, calc_safety_factor, find_appropriate_time

from wms import logger


class UGridDataset(Dataset, NetCDFDataset):

    @classmethod
    def is_valid(cls, uri):
        try:
            with EnhancedDataset(uri) as ds:
                return 'ugrid' in ds.Conventions.lower()
        except RuntimeError:
            try:
                with EnhancedMFDataset(uri, aggdim='time') as ds:
                    return 'ugrid' in ds.Conventions.lower()
            except (IndexError, AttributeError, RuntimeError, ValueError):
                return False
        except (FileNotFoundError, AttributeError):
            return False

    def has_grid_cache(self):
        return os.path.exists(self.topology_file)

    def has_time_cache(self):
        return caches['time'].get(self.time_cache_file) is not None

    def clear_cache(self):
        super().clear_cache()
        return caches['time'].delete(self.time_cache_file)

    def make_rtree(self):

        with self.dataset() as nc:
            ug = UGrid.from_nc_dataset(nc=nc)

            def rtree_faces_generator_function():
                for face_idx, node_list in enumerate(ug.faces):
                    nodes = ug.nodes[node_list]
                    xmin, ymin = np.min(nodes, 0)
                    xmax, ymax = np.max(nodes, 0)
                    yield (face_idx, (xmin, ymin, xmax, ymax), face_idx)

            logger.info("Building Faces Rtree Topology Cache for {0}".format(self.name))
            start = time.time()
            _, face_temp_file = tempfile.mkstemp(suffix='.face')
            pf = index.Property()
            pf.filename = str(face_temp_file)
            pf.overwrite = True
            pf.storage   = index.RT_Disk
            pf.dimension = 2
            idx = index.Index(pf.filename,
                              rtree_faces_generator_function(),
                              properties=pf,
                              interleaved=True,
                              overwrite=True)
            idx.close()
            logger.info("Built Faces Rtree Topology Cache in {0} seconds.".format(time.time() - start))
            shutil.move('{}.dat'.format(face_temp_file), self.face_tree_data_file)
            shutil.move('{}.idx'.format(face_temp_file), self.face_tree_index_file)

            def rtree_nodes_generator_function():
                for node_index, (x, y) in enumerate(ug.nodes):
                    yield (node_index, (x, y, x, y), node_index)
            logger.info("Building Nodes Rtree Topology Cache for {0}".format(self.name))
            start = time.time()
            _, node_temp_file = tempfile.mkstemp(suffix='.node')
            pn = index.Property()
            pn.filename = str(node_temp_file)
            pn.overwrite = True
            pn.storage   = index.RT_Disk
            pn.dimension = 2
            idx = index.Index(pn.filename,
                              rtree_nodes_generator_function(),
                              properties=pn,
                              interleaved=True,
                              overwrite=True)
            idx.close()
            logger.info("Built Nodes Rtree Topology Cache in {0} seconds.".format(time.time() - start))
            shutil.move('{}.dat'.format(node_temp_file), self.node_tree_data_file)
            shutil.move('{}.idx'.format(node_temp_file), self.node_tree_index_file)

    def update_time_cache(self):
        with self.dataset() as nc:
            if nc is None:
                logger.error("Failed update_time_cache, could not load dataset "
                             "as a netCDF4 object")
                return

            time_cache = {}
            layer_cache = {}
            time_vars = nc.get_variables_by_attributes(standard_name='time')
            for time_var in time_vars:
                time_cache[time_var.name] = nc4.num2date(
                    time_var[:],
                    time_var.units,
                    getattr(time_var, 'calendar', 'standard')
                )

            for ly in self.all_layers():
                try:
                    layer_cache[ly.access_name] = find_appropriate_time(nc.variables[ly.access_name], time_vars)
                except ValueError:
                    layer_cache[ly.access_name] = None

            full_cache = {'times': time_cache, 'layers': layer_cache}
            logger.info("Built time cache for {0}".format(self.name))
            caches['time'].set(self.time_cache_file, full_cache, None)
            return full_cache

    def update_grid_cache(self, force=False):
        with self.dataset() as nc:
            if nc is None:
                logger.error("Failed update_grid_cache, could not load dataset "
                             "as a netCDF4 object")
                return

            ug = UGrid.from_nc_dataset(nc=nc)

            # Atomic write
            tmphandle, tmpsave = tempfile.mkstemp()
            try:
                ug.save_as_netcdf(tmpsave)
            finally:
                os.close(tmphandle)
                if os.path.isfile(tmpsave):
                    shutil.move(tmpsave, self.topology_file)
                else:
                    logger.error("Failed to create topology_file cache for Dataset '{}'".format(self.dataset.name))
                    return

        # Now do the RTree index
        self.make_rtree()

    def minmax(self, layer, request):
        time_index, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']

        with self.dataset() as nc:
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
            spatial_idx = data_handler.ugrid_lat_lon_subset_idx(lon, lat, bbox=wgs84_bbox.bbox)

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
                    data = [
                        sqrt((u * u) + (v * v)) for (u, v,) in
                        data.T if u != np.nan and v != np.nan
                    ]
                    vmin = min(data)
                    vmax = max(data)

            return gmd_handler.from_dict(dict(min=vmin, max=vmax))

    def getmap(self, layer, request):
        time_index, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']

        with self.dataset() as nc:
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

            # Calculate any vector padding if we need to
            padding = None
            vector_step = request.GET['vectorstep']
            if request.GET['image_type'] == 'vectors':
                padding_factor = calc_safety_factor(request.GET['vectorscale'])
                padding = calc_lon_lat_padding(lon, lat, padding_factor) * vector_step

            # Calculate the boolean spatial mask to slice with
            bool_spatial_idx = data_handler.ugrid_lat_lon_subset_idx(lon, lat,
                                                                     bbox=wgs84_bbox.bbox,
                                                                     padding=padding)

            # Randomize vectors to subset if we need to
            if request.GET['image_type'] == 'vectors' and vector_step > 1:
                num_vec = int(bool_spatial_idx.size / vector_step)
                step = int(bool_spatial_idx.size / num_vec)
                bool_spatial_idx[np.where(bool_spatial_idx==True)][0::step] = False  # noqa: E225

            # If no triangles intersect the field of view, return a transparent tile
            if not np.any(bool_spatial_idx):
                logger.info("No triangles in field of view, returning empty tile.")
                return self.empty_response(layer, request)

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

                if request.GET['image_type'] in ['pcolor', 'contours', 'filledcontours']:
                    # Avoid triangles with nan values
                    bool_spatial_idx[np.isnan(data)] = False

                    # Get the faces to plot
                    faces = ug.faces[:]
                    face_idx = data_handler.face_idx_from_node_idx(faces, bool_spatial_idx)
                    faces_subset = faces[face_idx]
                    tri_subset = Tri.Triangulation(lon, lat, triangles=faces_subset)

                    if request.GET['image_type'] == 'pcolor':
                        return mpl_handler.tripcolor_response(tri_subset, data, request, data_location=data_location)
                    else:
                        return mpl_handler.tricontouring_response(tri_subset, data, request)
                elif request.GET['image_type'] in ['filledhatches', 'hatches']:
                    raise NotImplementedError('matplotlib does not support hatching on triangular grids... sorry!')
                else:
                    raise NotImplementedError('Image type "{}" is not supported.'.format(request.GET['image_type']))

            elif isinstance(layer, VirtualLayer):
                # Data needs to be [var1,var2] where var are 1D (nodes only, elevation and time already handled)
                data = []
                for l in layer.layers:
                    data_obj = nc.variables[l.var_name]
                    if (len(data_obj.shape) == 3):
                        z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                        data.append(data_obj[time_index, z_index, bool_spatial_idx])
                    elif (len(data_obj.shape) == 2):
                        data.append(data_obj[time_index, bool_spatial_idx])
                    elif len(data_obj.shape) == 1:
                        data.append(data_obj[bool_spatial_idx])
                    else:
                        logger.debug("Dimension Mismatch: data_obj.shape == {0} and time = {1}".format(data_obj.shape, time_value))
                        return self.empty_response(layer, request)

                if request.GET['image_type'] == 'vectors':
                    return mpl_handler.quiver_response(lon[bool_spatial_idx],
                                                       lat[bool_spatial_idx],
                                                       data[0],
                                                       data[1],
                                                       request)
                else:
                    raise NotImplementedError('Image type "{}" is not supported.'.format(request.GET['image_type']))

    def getfeatureinfo(self, layer, request):
        with self.dataset() as nc:
            data_obj = nc.variables[layer.access_name]
            data_location = data_obj.location

            geo_index, closest_x, closest_y, start_time_index, end_time_index, return_dates = self.setup_getfeatureinfo(layer, request, location=data_location)

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
                        data = data_obj[start_time_index:end_time_index, z_index, geo_index]
                    elif len(data_obj.shape) == 2:
                        data = data_obj[start_time_index:end_time_index, geo_index]
                    elif len(data_obj.shape) == 1:
                        data = data_obj[geo_index]
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

    def wgs84_bounds(self, layer):
        with self.dataset() as nc:
            try:
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

                minx = np.nanmin(coords[:, 0])
                miny = np.nanmin(coords[:, 1])
                maxx = np.nanmax(coords[:, 0])
                maxy = np.nanmax(coords[:, 1])

                return DotDict(minx=minx, miny=miny, maxx=maxx, maxy=maxy, bbox=(minx, miny, maxx, maxy))
            except AttributeError:
                pass

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
        time_cache = caches['time'].get(self.time_cache_file, {'times': {}, 'layers': {}})

        if layer.access_name not in time_cache['layers']:
            logger.error("No layer ({}) in time cache, returning nothing".format(layer.access_name))
            return []

        ltv = time_cache['layers'].get(layer.access_name)
        if ltv is None:
            # Legit this might not be a layer with time so just return empty list (no error message)
            return []

        if ltv in time_cache['times']:
            return time_cache['times'][ltv]
        else:
            logger.error("No time ({}) in time cache, returning nothing".format(ltv))
            return []

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

    def depth_direction(self, layer):
        d = self.depth_variable(layer)
        if d is not None:
            if hasattr(d, 'positive'):
                return d.positive
        return 'unknown'

    def depths(self, layer):
        d = self.depth_variable(layer)
        if d is not None:
            return range(0, d.shape[0])
        return []

    def humanize(self):
        return "UGRID"
