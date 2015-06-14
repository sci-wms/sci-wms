# -*- coding: utf-8 -*-
import os
import time
import bisect
import shutil
import tempfile
from datetime import datetime

import pytz

from pyugrid import UGrid
import pyproj
from pyaxiom.netcdf import EnhancedDataset
import numpy as np
import netCDF4

import pandas as pd

import matplotlib.tri as Tri

from django.http import HttpResponse

import rtree

from wms.models import Dataset, Layer, VirtualLayer
from wms.utils import DotDict

from wms import data_handler
from wms import mpl_handler
from wms import views

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

        _, temp_file = tempfile.mkstemp(suffix='.tree')

        nc = self.netcdf4_dataset()
        ug = UGrid.from_nc_dataset(nc=nc)

        class FastRtree(rtree.Rtree):
            def dumps(self, obj):
                try:
                    import cPickle
                    return cPickle.dumps(obj, -1)
                except ImportError:
                    super(FastRtree, self).dumps(obj)

        def rtree_generator_function():
            for face_idx, node_list in enumerate(ug.faces):
                nodes = ug.nodes[node_list]
                xmin, ymin = np.min(nodes, 0)
                xmax, ymax = np.max(nodes, 0)
                yield (face_idx, (xmin, ymin, xmax, ymax), node_list)

        logger.info("Building Rtree Topology Cache for {0}".format(self.name))
        start = time.time()
        FastRtree(temp_file,
                  rtree_generator_function(),
                  properties=p,
                  overwrite=True,
                  interleaved=True)
        logger.info("Built Rtree Topology Cache in {0} seconds.".format(time.time() - start))

        shutil.move(temp_file, self.node_tree_data_file)
        shutil.move(temp_file, self.node_file_index_file)

        nc.close()

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
                    cached_time_var.standard_name = 'time'
            cached_nc.close()

            # Now do the RTree index
            self.make_rtree()

        except RuntimeError:
            pass  # We could still be updating the cache file
        finally:
            if nc is not None:
                nc.close()

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

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

            spatial_idx = data_handler.lat_lon_subset_idx(lon, lat, wgs84_bbox.minx, wgs84_bbox.miny, wgs84_bbox.maxx, wgs84_bbox.maxy)

            face_indicies = ug.faces[:]
            face_indicies_spatial_idx = data_handler.faces_subset_idx(face_indicies, spatial_idx)

            # If no traingles insersect the field of view, return a transparent tile
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
                    return self.empty_response(layer, request)

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
                                                       request)
                else:
                    return self.empty_response(layer, request)
        finally:
            nc.close()

    def getlegendgraphic(self, layer, request):
        return views.getLegendGraphic(request, self)

    def getfeatureinfo(self, layer, request):
        try:
            nc = self.netcdf4_dataset()
            data_obj = nc.variables[layer.access_name]
            data_location = data_obj.location
            mesh_name = data_obj.mesh
            # Use local topology for pulling bounds data
            ug = UGrid.from_ncfile(self.topology_file, mesh_name=mesh_name)

            try:
                # Find closest cell or node (only node for now)
                tree = rtree.index.Index(self.node_tree_root)
                nindex = list(tree.nearest((tlon, tlat, tlon, tlat), 1, objects=True))[0]
                tree.close()
                closest_lon, clostest_lat = tuple(nindex.bbox[2:])
                closest_index = nindex.id
            except BaseException:
                logger.exception("Could not query Tree for nearest point")
            finally:
                tree.close()

            timevar = nc.get_variables_by_attributes(standard_name='time')[0]
            start_nc_num = round(netCDF4.date2num(request.GET['starting'], units=timevar.units))
            end_nc_num = round(netCDF4.date2num(request.GET['ending'], units=timevar.units))

            all_times = timevar[:]
            start_nc_index = bisect.bisect_right(all_times, start_nc_num) - 1
            end_nc_index = bisect.bisect_right(all_times, end_nc_num) - 1
            if start_nc_index == end_nc_index:
                end_nc_index += 1

            # Get the actual time values (for return)
            return_dates = netCDF4.num2daate(all_times[start_nc_index:end_nc_index], units=timevar.units)

            return_arrays = []
            z_value = None
            if isinstance(layer, Layer):
                if (len(data_obj.shape) == 3):
                    z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                    data = data_obj[start_nc_index:end_nc_index, z_index, :]
                elif (len(data_obj.shape) == 2):
                    data = data_obj[start_nc_index:end_nc_index, :]
                elif len(data_obj.shape) == 1:
                    data = data_obj[:]
                else:
                    raise ValueError("Dimension Mismatch: data_obj.shape == {0} and time indexes = {1} to {2}".format(data_obj.shape, start_nc_index, end_nc_index))

                return_arrays.append(data)

            elif isinstance(layer, VirtualLayer):

                # Data needs to be [var1,var2] where var are 1D (nodes only, elevation and time already handled)
                for l in layer.layers:
                    data_obj = nc.variables[l.var_name]
                    if (len(data_obj.shape) == 3):
                        z_index, z_value = self.nearest_z(layer, request.GET['elevation'])
                        data.append(data_obj[start_nc_index:end_nc_index, z_index, :])
                    elif (len(data_obj.shape) == 2):
                        data.append(data_obj[start_nc_index:end_nc_index, :])
                    elif len(data_obj.shape) == 1:
                        data.append(data_obj[:])
                    else:
                        raise ValueError("Dimension Mismatch: data_obj.shape == {0} and time indexes = {1} to {2}".format(data_obj.shape, start_nc_index, end_nc_index))

                    return_arrays.append(data)

            # Data is now in the return_arrays list, as a list of numpy arrays.  We need
            # to add time and depth to them to create a single Pandas DataFrame
            if (len(data_obj.shape) == 3):
                df = pd.DataFrame({'time': return_dates,
                                   'z': z_value})
            elif (len(data_obj.shape) == 2):
                df = pd.DataFrame({'time': return_dates})
            else:
                df = pd.DataFrame()
            # Now add a column for each member of the return_arrays list
            # ggsdgsdfsdfs

            if request.GET['info_format'] == 'text/csv':
                response = HttpResponse(content_type='text/csv')
                response.write(df.something)
            elif request.GET['info_format'] == 'text/tsv':
                response = HttpResponse(content_type='text/csv')
                response.write(df.something)
            elif request.GET['info_format'] == 'application/x-hdf5':
                response = HttpResponse(content_type='text/csv')
                response.write(df.something)

        except BaseException:
            logger.exception("Could not process GetFeatureInfo request")
        finally:
            nc.close()

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
