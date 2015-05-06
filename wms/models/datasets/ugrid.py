# -*- coding: utf-8 -*-
import os
import bisect
from datetime import datetime

import pytz

from pyugrid import UGrid
import pyproj
from pyaxiom.netcdf import EnhancedDataset
import numpy as np
import netCDF4

import matplotlib.tri as Tri

from django.http import HttpResponse

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

    def getmap(self, layer, request):
        time_index, time_value = self.nearest_time(layer, request.GET['time'])

        # Transform bbox to WGS84
        EPSG4326 = pyproj.Proj(init='EPSG:4326')
        bbox = request.GET['bbox']
        wgs84_minx, wgs84_miny = pyproj.transform(request.GET['crs'], EPSG4326, bbox.minx, bbox.miny)
        wgs84_maxx, wgs84_maxy = pyproj.transform(request.GET['crs'], EPSG4326, bbox.maxx, bbox.maxy)

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

            spatial_idx = data_handler.lat_lon_subset_idx(lon, lat, wgs84_minx, wgs84_miny, wgs84_maxx, wgs84_maxy)

            face_indicies = ug.faces[:]
            face_indicies_spatial_idx = data_handler.faces_subset_idx(face_indicies, spatial_idx)

            # If no traingles insersect the field of view, return a transparent tile
            if (len(spatial_idx) == 0) or (len(face_indicies_spatial_idx) == 0):
                logger.debug("No triangles in field of view, returning empty tile.")
                canvas = data_handler.blank_canvas(request.GET['width'], request.GET['height'])
                response = HttpResponse(content_type='image/png')
                canvas.print_png(response)
                return response

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
                    canvas = data_handler.blank_canvas(request.GET.get['width'], request.GET['height'])
                    HttpResponse(content_type='image/png')
                    canvas.print_png(response)
                    return response

                if request.GET['image_type'] == 'filledcontours':
                    return mpl_handler.tricontourf_response(tri_subset, data, request)

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
                        canvas = data_handler.blank_canvas(request.GET.get['width'], request.GET['height'])
                        HttpResponse(content_type='image/png')
                        canvas.print_png(response)
                        return response

                if request.GET['image_type'] == 'vectors':
                    return mpl_handler.quiver_response(lon[spatial_idx],
                                                       lat[spatial_idx],
                                                       data[0][spatial_idx],
                                                       data[1][spatial_idx],
                                                       request)
        finally:
            nc.close()

    def getlegendgraphic(self, layer, request):
        return views.getLegendGraphic(request, self)

    def getfeatureinfo(self, layer, request):
        return views.getFeatureInfo(request, self)

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
        depth_index = bisect.bisect_right(depths, z)
        try:
            return depth_index, depths[depth_index]
        except IndexError:
            return depth_index - 1, depths[depth_index - 1]  # Would have added to the end

    def nearest_time(self, layer, time):
        """
        Return the time index and time value that is closest
        """
        try:
            nc = self.topology_dataset()
            time_var = nc.variables['time']
            units = time_var.units
            if hasattr(time_var, 'calendar'):
                calendar = time_var.calendar
            else:
                calendar = 'gregorian'
            num_date = round(netCDF4.date2num(time, units=units, calendar=calendar))

            times = time_var[:]
            time_index = bisect.bisect_right(times, num_date)
            try:
                return time_index, times[time_index]
            except IndexError:
                return time_index - 1, times[time_index - 1]  # Would have added to the end
        finally:
            nc.close()

    def times(self, layer):
        try:
            nc = self.topology_dataset()
            return netCDF4.num2date(nc.variables['time'][:], units=nc.variables['time'].units)
        finally:
            nc.close()

    def depth_variable(self, layer):
        try:
            nc = self.netcdf4_dataset()
            layer_var = nc.variables[layer.access_name]
            for cv in layer_var.coordinates.split():
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
                dvar = nc.variables[d]
                if hasattr(dvar, 'positive'):
                    return dvar.positive
            finally:
                nc.close()
        return 'unknown'

    def depths(self, layer):
        d = self.depth_variable(layer)
        if d is not None:
            try:
                nc = self.netcdf4_dataset()
                return range(0, nc.variables[d].shape[0])
            finally:
                nc.close()
        return []

    def humanize(self):
        return "UGRID"
