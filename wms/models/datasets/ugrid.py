# -*- coding: utf-8 -*-
import os
from datetime import datetime

import pytz

from pyugrid import UGrid
from pyaxiom.netcdf import EnhancedDataset
import numpy as np
import netCDF4

from wms.models import Dataset
from wms.utils import DotDict

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
        return views.getMap(request, self)

    def getlegendgraphic(self, layer, request):
        return views.getLegendGraphic(request, self)

    def getfeatureinfo(self, layer, request):
        return views.getFeatureInfo(request, self)

    def wgs84_bounds(self, layer):
        try:
            nc = self.netcdf4_dataset()
            data_location = nc.variables[layer.var_name].location
            mesh_name = nc.variables[layer.var_name].mesh
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

    def times(self, layer):
        try:
            nc = self.topology_dataset()
            return netCDF4.num2date(nc.variables['time'][:], units=nc.variables['time'].units)
        finally:
            nc.close()

    def depth_variable(self, layer):
        try:
            nc = self.netcdf4_dataset()
            layer_var = nc.variables[layer.var_name]
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
