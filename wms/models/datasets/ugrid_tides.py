# -*- coding: utf-8 -*-
import os
import calendar
from datetime import datetime, timedelta

import pytz

from pyugrid import UGrid
import netCDF4
import numpy as np

from wms.models import Style

from wms.models import UGridDataset, VirtualLayer
from wms.utils import calc_lon_lat_padding, calc_safety_factor, timeit, DotDict

from wms import data_handler
from wms import mpl_handler
from wms import gfi_handler
from wms import gmd_handler

from wms import logger


class UGridTideDataset(UGridDataset):

    @classmethod
    def is_valid(cls, uri):
        try:
            with netCDF4.Dataset(uri) as ds:
                return 'utides' in ds.Conventions.lower()
        except (RuntimeError, AttributeError):
            return False

    def update_cache(self, force=False):
        with self.dataset() as nc:
            ug = UGrid.from_nc_dataset(nc)
            ug.save_as_netcdf(self.topology_file)

            if not os.path.exists(self.topology_file):
                logger.error("Failed to create topology_file cache for Dataset '{}'".format(self.dataset))
                return

            uamp = nc.get_variables_by_attributes(standard_name='eastward_sea_water_velocity_amplitude')[0]
            vamp = nc.get_variables_by_attributes(standard_name='northward_sea_water_velocity_amplitude')[0]
            uphase = nc.get_variables_by_attributes(standard_name='eastward_sea_water_velocity_phase')[0]
            vphase = nc.get_variables_by_attributes(standard_name='northward_sea_water_velocity_phase')[0]
            tnames = nc.get_variables_by_attributes(standard_name='tide_constituent')[0]
            tfreqs = nc.get_variables_by_attributes(standard_name='tide_frequency')[0]

            with netCDF4.Dataset(self.topology_file, mode='a') as cnc:

                ntides = uamp.shape[uamp.dimensions.index('ntides')]
                nlocs = uamp.shape[uamp.dimensions.index(uamp.location)]
                cnc.createDimension('ntides', ntides)
                cnc.createDimension('maxStrlen64', 64)

                vdims = ('ntides', '{}_num_{}'.format(uamp.mesh, uamp.location))

                # Swap ntides to always be the first dimension.. it can be the second in the source files!
                transpose = False
                if uamp.shape[0] > uamp.shape[1]:
                    logger.info("Found flipped dimensions in source file... fixing in local cache.")
                    transpose = True

                # We are changing the variable names to 'u' and 'v' from 'u_amp' and 'v_amp' so
                # the layer.access_method can find the variable from the virtual layer 'u,v'
                ua = cnc.createVariable('u', uamp.dtype, vdims, zlib=True, fill_value=uamp._FillValue, chunksizes=[1, nlocs/4])
                for x in uamp.ncattrs():
                    if x != '_FillValue':
                        ua.setncattr(x, uamp.getncattr(x))
                va = cnc.createVariable('v', vamp.dtype, vdims, zlib=True, fill_value=vamp._FillValue, chunksizes=[1, nlocs/4])
                for x in vamp.ncattrs():
                    if x != '_FillValue':
                        va.setncattr(x, vamp.getncattr(x))
                up = cnc.createVariable('u_phase', uphase.dtype, vdims, zlib=True, fill_value=uphase._FillValue, chunksizes=[1, nlocs/4])
                for x in uphase.ncattrs():
                    if x != '_FillValue':
                        up.setncattr(x, uphase.getncattr(x))
                vp = cnc.createVariable('v_phase', vphase.dtype, vdims, zlib=True, fill_value=vphase._FillValue, chunksizes=[1, nlocs/4])
                for x in vphase.ncattrs():
                    if x != '_FillValue':
                        vp.setncattr(x, vphase.getncattr(x))

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
                    if transpose is True:
                        ua[r, :] = uamp[:, r].T
                        va[r, :] = vamp[:, r].T
                        up[r, :] = uphase[:, r].T
                        vp[r, :] = vphase[:, r].T
                    else:
                        ua[r, :] = uamp[r, :]
                        va[r, :] = vamp[r, :]
                        up[r, :] = uphase[r, :]
                        vp[r, :] = vphase[r, :]

        # Now do the RTree index
        #self.make_rtree()

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    def minmax(self, layer, request):
        _, time_value = self.nearest_time(layer, request.GET['time'])
        wgs84_bbox = request.GET['wgs84_bbox']
        us, vs, _, _ = self.get_tidal_vectors(layer, time=time_value, bbox=wgs84_bbox.bbox)
        magnitude = np.sqrt((us*us) + (vs*vs))
        return gmd_handler.from_dict(dict(min=np.min(magnitude), max=np.max(magnitude)))

    def get_tidal_vectors(self, layer, time, bbox, vector_scale=None, vector_step=None):

        vector_scale = vector_scale or 1
        vector_step = vector_step or 1

        with netCDF4.Dataset(self.topology_file) as nc:
            data_obj = nc.variables[layer.access_name]
            data_location = data_obj.location
            mesh_name = data_obj.mesh

            ug = UGrid.from_nc_dataset(nc, mesh_name=mesh_name)
            coords = np.empty(0)
            if data_location == 'node':
                coords = ug.nodes
            elif data_location == 'face':
                coords = ug.face_coordinates
            elif data_location == 'edge':
                coords = ug.edge_coordinates

            lon = coords[:, 0]
            lat = coords[:, 1]

            padding_factor = calc_safety_factor(vector_scale)
            padding = calc_lon_lat_padding(lon, lat, padding_factor) * vector_step
            spatial_idx = data_handler.ugrid_lat_lon_subset_idx(lon, lat,
                                                                bbox=bbox,
                                                                padding=padding)

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

        vector_scale = None
        vector_step = None

        if request.GET['image_type'] == 'vectors':
            vector_scale = request.GET['vectorscale']
            vector_step = request.GET['vectorstep']

        us, vs, lons, lats = self.get_tidal_vectors(layer,
                                                    time=time_value,
                                                    bbox=request.GET['wgs84_bbox'].bbox,
                                                    vector_scale=vector_scale,
                                                    vector_step=vector_step)

        if request.GET['image_type'] == 'vectors':
            return mpl_handler.quiver_response(lons, lats, us, vs, request)
        else:
            raise NotImplementedError('Image type "{}" is not supported.'.format(request.GET['image_type']))

    def getfeatureinfo(self, layer, request):
        raise NotImplementedError("No GFI support for UGRID-TIDES (yet)")

    def analyze_virtual_layers(self):
        vl, created = VirtualLayer.objects.get_or_create(var_name='u,v', dataset_id=self.pk)
        vl.std_name = 'barotropic_sea_water_velocity'
        vl.units = 'm/s'
        vl.description = "Barotropic sea water velocity from tidal constituents"

        if created is True:
            vl.active = True
            vl.styles.add(Style.objects.get(colormap='cubehelix', image_type='vectors'))

        vl.save()

    def process_layers(self):
        self.analyze_virtual_layers()

    def nearest_time(self, layer, time):
        return None, time

    def times(self, layer):
        return datetime.utcnow().replace(tzinfo=pytz.utc)

    def wgs84_bounds(self, layer):
        with netCDF4.Dataset(self.topology_file) as nc:
            try:
                data_location = nc.variables['u'].location
                mesh_name = nc.variables['u'].mesh
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

    def time_windows(self, layer):
        s = datetime.utcnow().replace(second=0, minute=0, microsecond=0, tzinfo=pytz.utc) - timedelta(days=365*100)
        e = datetime.utcnow().replace(second=0, minute=0, microsecond=0, tzinfo=pytz.utc) + timedelta(days=365*100)
        d = timedelta(minutes=5)
        return [(s, e, d)]

    def depth_variable(self, layer):
        return None

    def humanize(self):
        return "UTIDES"
