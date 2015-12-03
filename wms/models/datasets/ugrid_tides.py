# -*- coding: utf-8 -*-
import os
import time
import bisect
import shutil
import tempfile
import calendar
import itertools
from math import sqrt
from datetime import datetime

import pytz

from pyugrid import UGrid
from pyaxiom.netcdf import EnhancedDataset, EnhancedMFDataset
import numpy as np
import netCDF4

from wms.models import Style

import pandas as pd

import matplotlib.tri as Tri

from rtree import index

from wms.models import Dataset, Layer, VirtualLayer, NetCDFDataset
from wms.utils import DotDict, calc_lon_lat_padding, calc_safety_factor, find_appropriate_time

from wms import data_handler
from wms import mpl_handler
from wms import gfi_handler
from wms import gmd_handler

from wms import logger


class UGridTideDataset(Dataset, NetCDFDataset):

    @classmethod
    def is_valid(cls, uri):
        try:
            with EnhancedDataset(uri) as ds:
                return 'ugrid' in ds.Conventions.lower()
        except RuntimeError:
            try:
                with EnhancedMFDataset(uri, aggdim='time') as ds:
                    return 'ugrid' in ds.Conventions.lower()
            except (AttributeError, RuntimeError):
                return False
        except AttributeError:
            return False

    def has_cache(self):
        return os.path.exists(self.topology_file)

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
            idx = index.Index(pf.filename.decode('utf-8'),
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
            idx = index.Index(pn.filename.decode('utf-8'),
                              rtree_nodes_generator_function(),
                              properties=pn,
                              interleaved=True,
                              overwrite=True)
            idx.close()
            logger.info("Built Nodes Rtree Topology Cache in {0} seconds.".format(time.time() - start))
            shutil.move('{}.dat'.format(node_temp_file), self.node_tree_data_file)
            shutil.move('{}.idx'.format(node_temp_file), self.node_tree_index_file)

    def update_cache(self, force=False):
        with self.dataset() as nc:
            ug = UGrid.from_nc_dataset(nc=nc)
            ug.save_as_netcdf(self.topology_file)

            if not os.path.exists(self.topology_file):
                logger.error("Failed to create topology_file cache for Dataset '{}'".format(self.dataset))
                return

            with EnhancedDataset(self.topology_file, mode='a') as cnc:

                uamp = nc.get_variables_by_attributes(standard_name='eastward_sea_water_velocity_amplitude')[0]
                vamp = nc.get_variables_by_attributes(standard_name='northward_sea_water_velocity_amplitude')[0]
                uphase = nc.get_variables_by_attributes(standard_name='eastward_sea_water_velocity_phase')[0]
                vphase = nc.get_variables_by_attributes(standard_name='northward_sea_water_velocity_phase')[0]
                tnames = nc.get_variables_by_attributes(standard_name='tide_constituent')[0]
                tfreqs = nc.get_variables_by_attributes(standard_name='tide_frequency')[0]

                mesh_name = uamp.mesh

                ntides = uamp.shape[uamp.dimensions.index('ntides')]
                cnc.createDimension('ntides', ntides)
                cnc.createDimension('maxStrlen64', 64)

                # We are changing the variable names to 'u' and 'v' from 'u_amp' and 'v_amp' so
                # the layer.access_method can find the variable from the virtual layer 'u,v'
                ua = cnc.createVariable('u', uamp.dtype, ('ntides', '{}_num_node'.format(mesh_name)), zlib=True, fill_value=uamp._FillValue)
                for x in uamp.ncattrs():
                    if x != '_FillValue':
                        ua.setncattr(x, uamp.getncattr(x))
                va = cnc.createVariable('v', vamp.dtype, ('ntides', '{}_num_node'.format(mesh_name)), zlib=True, fill_value=vamp._FillValue)
                for x in vamp.ncattrs():
                    if x != '_FillValue':
                        ua.setncattr(x, vamp.getncattr(x))
                up = cnc.createVariable('u_phase', uphase.dtype, ('ntides', '{}_num_node'.format(mesh_name)), zlib=True, fill_value=uphase._FillValue)
                for x in uphase.ncattrs():
                    if x != '_FillValue':
                        ua.setncattr(x, uphase.getncattr(x))
                vp = cnc.createVariable('v_phase', vphase.dtype, ('ntides', '{}_num_node'.format(mesh_name)), zlib=True, fill_value=vphase._FillValue)
                for x in vphase.ncattrs():
                    if x != '_FillValue':
                        ua.setncattr(x, vphase.getncattr(x))

                tc = cnc.createVariable('tidenames', tnames.dtype, tnames.dimensions)
                tc[:] = tnames[:]
                for x in tnames.ncattrs():
                    if x != '_FillValue':
                        tc.setncattr(x, tnames.getncattr(x))

                tf = cnc.createVariable('tidefreqs', tfreqs.dtype, ('ntides',))
                tf[:] = tfreqs[:]
                for x in tfreqs.ncattrs():
                    if x != '_FillValue':
                        tf.setncattr(x, tfreqs.getncattr(x))

                for r in range(ntides):
                    logger.info("Saving ntide {} into cache".format(r))
                    ua[:, r] = uamp[r, :]
                    va[:, r] = vamp[r, :]
                    up[:, r] = uphase[r, :]
                    vp[:, r] = vphase[r, :]

            # Now do the RTree index
            self.make_rtree()

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    def minmax(self, layer, request):
        _, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']
        us, vs, _, _ = self.get_tidal_vectors(layer, time=time_value, bbox=(wgs84_bbox.minx, wgs84_bbox.miny, wgs84_bbox.maxx, wgs84_bbox.maxy))

        return gmd_handler.from_dict(dict(min=np.min(us), max=np.max(us)))

    def get_tidal_vectors(self, layer, time, bbox):

        with EnhancedDataset(self.topology_file) as nc:
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

            land = np.logical_and
            spatial_idx = land(land(lon >= bbox[0], lon <= bbox[2]),
                               land(lat >= bbox[1], lat <= bbox[3]))

            tnames = nc.get_variables_by_attributes(standard_name='tide_constituent')[0]
            tfreqs = nc.get_variables_by_attributes(standard_name='tide_frequency')[0]

            from utide import _ut_constants_fname
            from utide.utilities import loadmatbunch
            con_info = loadmatbunch(_ut_constants_fname)['const']

            # Get names from the utide constant file
            utide_const_names = [ e.strip() for e in con_info['name'].tolist() ]

            # netCDF4-python is returning ugly arrays of bytes...
            names = []
            for n in tnames[:]:
                z = ''.join([ x.decode('utf-8') for x in n.tolist() if x ]).strip()
                names.append(z)

            if 'STEADY' in names:
                names[names.index('STEADY')] = 'Z0'
            extract_names = list(set(utide_const_names).intersection(set(names)))

            ntides = data_obj.shape[data_obj.dimensions.index('ntides')]
            extract_mask = np.zeros(shape=(ntides,), dtype=bool)
            for n in extract_names:
                extract_mask[names.index(n)] = True

            ua = nc.variables['u'][extract_mask, spatial_idx]
            va = nc.variables['v'][extract_mask, spatial_idx]
            up = nc.variables['u_phase'][extract_mask, spatial_idx]
            vp = nc.variables['v_phase'][extract_mask, spatial_idx]
            freqs = tfreqs[extract_mask]

            omega = freqs * 3600  # Convert from radians/s to radians/hour.

            from utide.harmonics import FUV
            from matplotlib.dates import date2num
            v, u, f = FUV(t=np.array([date2num(time) + 366.1667]),
                          tref=np.array([0]),
                          lind=np.array([ utide_const_names.index(x) for x in extract_names ]),
                          lat=55,  # Reference latitude for 3rd order satellites (degrees) (55 is fine always)
                          ngflgs=[0, 0, 0, 0])  # [NodsatLint NodsatNone GwchLint GwchNone]

            s = calendar.timegm(time.timetuple()) / 60 / 60.
            v, u, f = map(np.squeeze, (v, u, f))
            v = v * 2 * np.pi  # Convert phase in radians.
            u = u * 2 * np.pi  # Convert phase in radians.

            U = (f * ua.T * np.cos(v + s * omega + u - up.T * np.pi / 180)).sum(axis=1)
            V = (f * va.T * np.cos(v + s * omega + u - vp.T * np.pi / 180)).sum(axis=1)

            return U, V, lon[spatial_idx], lat[spatial_idx]

    def getmap(self, layer, request):
        _, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']
        us, vs, lons, lats = self.get_tidal_vectors(layer, time=time_value, bbox=(wgs84_bbox.minx, wgs84_bbox.miny, wgs84_bbox.maxx, wgs84_bbox.maxy))

        logger.info(us)

        return mpl_handler.quiver_response(lons,
                                           lats,
                                           us,
                                           vs,
                                           request,
                                           1
                                           )

    def getfeatureinfo(self, layer, request):
        with self.dataset() as nc:
            with self.topology() as topo:
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

                return DotDict(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
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
            return netCDF4.num2date(time_var[:], units=time_var.units)

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
        return "UGRID-TIDES"

    def analyze_virtual_layers(self):
        vl = VirtualLayer.objects.create(var_name='u,v',
                                         std_name='barotropic_sea_water_velocity',
                                         units='m/s',
                                         description="Barotropic sea water velocity from tidal constituents",
                                         dataset_id=self.pk,
                                         active=True)
        vl.styles.add(Style.objects.get(colormap='cubehelix', image_type='vectors'))
        vl.save()

    def process_layers(self):
        self.analyze_virtual_layers()

    def nearest_time(self, layer, time):
        return None, time
