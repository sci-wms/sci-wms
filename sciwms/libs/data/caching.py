'''
COPYRIGHT 2010 RPS ASA

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.

Created on Sep 6, 2011

@author: ACrosby

!!!THIS IS NOT A SCRIPT ANYMORE!!!
'''
from dateutil.parser import parse
from netCDF4 import Dataset as ncDataset
from netCDF4 import date2num
import sys
import os
import numpy
import logging
import traceback
from datetime import datetime
import numpy as np
from sciwms.apps.wms.models import Dataset
from sciwms.libs.data import build_tree
import multiprocessing
from collections import deque
import shutil
try:
    import cPickle as pickle
except:
    import Pickle as pickle

from django.conf import settings
from sciwms import logger

time_units = 'hours since 1970-01-01'


def create_topology(dataset_name, url, lat_var='lat', lon_var='lon'):
    try:
        #with s1:
        nclocalpath = os.path.join(settings.TOPOLOGY_PATH, dataset_name+".nc.updating")
        nc = ncDataset(url)
        nclocal = ncDataset(nclocalpath, mode="w", clobber=True)
        if "nv" in nc.variables:
            logger.info("identified as fvcom")
            grid = 'False'

            nclocal.createDimension('cell', nc.variables['latc'].shape[0])
            nclocal.createDimension('node', nc.variables['lat'].shape[0])
            nclocal.createDimension('time', nc.variables['time'].shape[0])
            nclocal.createDimension('corners', nc.variables['nv'].shape[0])

            lat = nclocal.createVariable('lat', 'f', ('node',), chunksizes=nc.variables['lat'].shape, zlib=False, complevel=0)
            lon = nclocal.createVariable('lon', 'f', ('node',), chunksizes=nc.variables['lat'].shape, zlib=False, complevel=0)
            latc = nclocal.createVariable('latc', 'f', ('cell',), chunksizes=nc.variables['latc'].shape, zlib=False, complevel=0)
            lonc = nclocal.createVariable('lonc', 'f', ('cell',), chunksizes=nc.variables['latc'].shape, zlib=False, complevel=0)
            nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=nc.variables['nv'].shape, zlib=False, complevel=0)

            time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=nc.variables['time'].shape, zlib=False, complevel=0)
            logger.info("done creating")
            lontemp = nc.variables['lon'][:]
            lonctemp = nc.variables['lonc'][:]

            if np.max(lontemp) > 180:
                lontemp[lontemp > 180] = lontemp[lontemp > 180] - 360
                lon[:] = np.asarray(lontemp)
            #elif np.min(lontemp) < -180:
            #    print "lessthan"
            #    lon[:] = np.asarray(lontemp) + 360
            #    lonc[:] = np.asarray(nc.variables['lonc'][:] + 360)
            else:
                lon[:] = lontemp
            if np.max(lonctemp) > 180:
                lonctemp[lonctemp > 180] = lonctemp[lonctemp > 180] - 360
                lonc[:] = np.asarray(lonctemp)
            else:
                lonc[:] = lonctemp

            lat[:] = nc.variables['lat'][:]
            latc[:] = nc.variables['latc'][:]

            nv[:, :] = nc.variables['nv'][:, :]
            logger.info("done filling vars")
            # DECODE the FVCOM datetime string (Time) and save as a high precision datenum
            timestrs = nc.variables['Times'][:]  # Format: "2013-01-15T00:00:00.000000"
            dates = [datetime.strptime(timestrs[i, :].tostring().replace('\0', ""), "%Y-%m-%dT%H:%M:%S.%f") for i in range(len(timestrs[:, 0]))]
            time[:] = date2num(dates, units=time_units)  # Use netCDF4's date2num function
            #time[:] = nc.variables['time'][:]
            logger.info("done time conversion")
            time.units = time_units
            #time.units = nc.variables['time'].units
            nclocal.sync()
            nclocal.grid = grid
            nclocal.sync()
            logger.info("data written to file")

        elif "element" in nc.variables:
            logger.info("identified as adcirc")
            grid = 'False'
            nclocal.createDimension('node', nc.variables['x'].shape[0])
            nclocal.createDimension('cell', nc.variables['element'].shape[0])
            nclocal.createDimension('time', nc.variables['time'].shape[0])
            nclocal.createDimension('corners', nc.variables['element'].shape[1])

            lat = nclocal.createVariable('lat', 'f', ('node',), chunksizes=(nc.variables['x'].shape[0],), zlib=False, complevel=0)
            lon = nclocal.createVariable('lon', 'f', ('node',), chunksizes=(nc.variables['x'].shape[0],), zlib=False, complevel=0)
            latc = nclocal.createVariable('latc', 'f', ('cell',), chunksizes=(nc.variables['element'].shape[0],), zlib=False, complevel=0)
            lonc = nclocal.createVariable('lonc', 'f', ('cell',), chunksizes=(nc.variables['element'].shape[0],), zlib=False, complevel=0)
            #if nc.variables['element'].shape[0] == 3:
            #    nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=nc.variables['element'].shape, zlib=False, complevel=0)
            #    nv[:,:] = nc.variables['element'][:,:]
            #else:
            nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=nc.variables['element'].shape[::-1], zlib=False, complevel=0)

            time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=nc.variables['time'].shape, zlib=False, complevel=0)

            lattemp = nc.variables['y'][:]
            lontemp = nc.variables['x'][:]
            lat[:] = lattemp
            lontemp[lontemp > 180] = lontemp[lontemp > 180] - 360

            lon[:] = lontemp
            import matplotlib.tri as Tri
            tri = Tri.Triangulation(lontemp,
                                    lattemp,
                                    nc.variables['element'][:, :]-1
                                    )

            lonc[:] = lontemp[tri.triangles].mean(axis=1)
            latc[:] = lattemp[tri.triangles].mean(axis=1)
            nv[:, :] = nc.variables['element'][:, :].T
            time[:] = nc.variables['time'][:]
            time.units = nc.variables['time'].units
            nclocal.sync()
            nclocal.grid = grid
            nclocal.sync()
            logger.info("data written to file")
        elif "ele" in nc.variables:
            for varname in nc.variables.iterkeys():
                if "mesh" in varname:
                    meshcoords = nc.variables[varname].node_coordinates.split(" ")
                    lonname, latname = meshcoords[0], meshcoords[1]
            logger.info("identified as selfe")
            grid = 'False'
            nclocal.createDimension('node', nc.variables['x'].shape[0])
            nclocal.createDimension('cell', nc.variables['ele'].shape[1])
            nclocal.createDimension('time', nc.variables['time'].shape[0])
            nclocal.createDimension('corners', nc.variables['ele'].shape[0])

            lat = nclocal.createVariable('lat', 'f', ('node',), chunksizes=(nc.variables['x'].shape[0],), zlib=False, complevel=0)
            lon = nclocal.createVariable('lon', 'f', ('node',), chunksizes=(nc.variables['x'].shape[0],), zlib=False, complevel=0)
            latc = nclocal.createVariable('latc', 'f', ('cell',), chunksizes=(nc.variables['ele'].shape[1],), zlib=False, complevel=0)
            lonc = nclocal.createVariable('lonc', 'f', ('cell',), chunksizes=(nc.variables['ele'].shape[1],), zlib=False, complevel=0)
            #if nc.variables['element'].shape[0] == 3:
            #    nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=nc.variables['element'].shape, zlib=False, complevel=0)
            #    nv[:,:] = nc.variables['element'][:,:]
            #else:
            nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=nc.variables['ele'].shape, zlib=False, complevel=0)
            time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=nc.variables['time'].shape, zlib=False, complevel=0)

            lattemp = nc.variables[latname][:]
            lontemp = nc.variables[lonname][:]
            lat[:] = lattemp
            lontemp[lontemp > 180] = lontemp[lontemp > 180] - 360

            lon[:] = lontemp
            import matplotlib.tri as Tri
            tri = Tri.Triangulation(lontemp,
                                    lattemp,
                                    nc.variables['ele'][:, :].T-1
                                    )

            lonc[:] = lontemp[tri.triangles].mean(axis=1)
            latc[:] = lattemp[tri.triangles].mean(axis=1)
            nv[:, :] = nc.variables['ele'][:, :]
            time[:] = nc.variables['time'][:]
            time.units = nc.variables['time'].units
            nclocal.sync()
            nclocal.grid = grid
            nclocal.sync()
            logger.info("data written to file")
        else:
            logger.info("identified as grid")
            latname, lonname = lat_var, lon_var
            if latname not in nc.variables:
                for key in nc.variables.iterkeys():
                    try:
                        nc.variables[key].__getattr__('units')
                        temp_units = nc.variables[key].units
                        if (not '_u' in key) and (not '_v' in key) and (not '_psi' in key):
                            if 'degree' in temp_units:
                                if 'east' in temp_units:
                                    lonname = key
                                elif 'north' in temp_units:
                                    latname = key
                                else:
                                    raise ValueError("No valid coordinates found in source netcdf file")
                    except:
                        pass
            if nc.variables[latname].ndim > 1:
                igrid = nc.variables[latname].shape[0]
                jgrid = nc.variables[latname].shape[1]
                grid = 'cgrid'
            else:
                grid = 'rgrid'
                igrid = nc.variables[latname].shape[0]
                jgrid = nc.variables[lonname].shape[0]
            latchunk, lonchunk = (igrid, jgrid,), (igrid, jgrid,)
            logger.info("native grid style identified")
            nclocal.createDimension('igrid', igrid)
            nclocal.createDimension('jgrid', jgrid)
            if "time" in nc.variables:
                nclocal.createDimension('time', nc.variables['time'].shape[0])
                if nc.variables['time'].ndim > 1:
                    time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=(nc.variables['time'].shape[0],), zlib=False, complevel=0)
                else:
                    time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=nc.variables['time'].shape, zlib=False, complevel=0)
            else:
                nclocal.createDimension('time', 1)
                time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=(1,), zlib=False, complevel=0)

            lat = nclocal.createVariable('lat', 'f', ('igrid', 'jgrid',), chunksizes=latchunk, zlib=False, complevel=0)
            lon = nclocal.createVariable('lon', 'f', ('igrid', 'jgrid',), chunksizes=lonchunk, zlib=False, complevel=0)
            logger.info("variables created in cache")
            lontemp = nc.variables[lonname][:]
            lontemp[lontemp > 180] = lontemp[lontemp > 180] - 360

            if grid == 'rgrid':
                lon[:], lat[:] = np.meshgrid(lontemp, nc.variables[latname][:])
                grid = 'cgrid'
            else:
                lon[:] = lontemp
                lat[:] = nc.variables[latname][:]
            if "time" in nc.variables:
                if nc.variables['time'].ndim > 1:
                    _str_data = nc.variables['time'][:, :]
                    #print _str_data.shape, type(_str_data), "''", str(_str_data[0,:].tostring().replace(" ","")), "''"
                    dates = [parse(_str_data[i, :].tostring()) for i in range(len(_str_data[:, 0]))]
                    time[:] = date2num(dates, time_units)
                    time.units = time_units
                else:
                    time[:] = nc.variables['time'][:]
                    time.units = nc.variables['time'].units
            else:
                time[:] = np.ones(1)
                time.units = time_units
            logger.info("data written to file")
            while not 'grid' in nclocal.ncattrs():
                nclocal.__setattr__('grid', 'cgrid')
                nclocal.sync()
            nclocal.sync()

        shutil.move(nclocalpath, nclocalpath.replace(".updating", ""))
        if not ((os.path.exists(nclocalpath.replace(".updating", "").replace(".nc", '_nodes.dat')) and os.path.exists(nclocalpath.replace(".updating", "").replace(".nc", "_nodes.idx")))):
            #with s1:
            build_tree.build_from_nc(nclocalpath.replace(".updating", ""))
        if grid == 'False':
            if not os.path.exists(nclocalpath.replace(".updating", "")[:-3] + '.domain'):
                #with s2:
                create_domain_polygon(nclocalpath.replace(".updating", ""))

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error("Disabling Error: " + repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        try:
            nclocal.close()
        except:
            pass
        try:
            nc.close()
        except:
            pass
        if os.path.exists(nclocalpath):
            os.unlink(nclocalpath)
        raise
    finally:
        nclocal.close()
        nc.close()


def create_topology_from_config():
    """
    Initialize topology upon server start up for each of the datasets listed in LOCALDATASETPATH dictionary
    """
    for dataset in Dataset.objects.all():
        print "Adding: " + dataset["name"]
        create_topology(dataset["name"], dataset["uri"])


def update_datasets():
    for d in Dataset.objects.all():
        try:
            logger.info("Updating %s" % d.name)
            update_dataset_cache(d)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error("Disabling Error: " + repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))


def update_dataset_cache(dataset):
    try:
        try:
            filemtime = datetime.fromtimestamp(
                os.path.getmtime(
                    os.path.join(
                        settings.TOPOLOGY_PATH, dataset.name + ".nc"
                    )))
            if dataset.keep_up_to_date:
                try:
                    nc = ncDataset(dataset.path())
                    topo = ncDataset(os.path.join(
                        settings.TOPOLOGY_PATH, dataset.name + ".nc"))

                    time1 = nc.variables['time'][-1]
                    time2 = topo.variables['time'][-1]
                    if time1 != time2:
                        logger.info("Updating: " + dataset.path())
                        create_topology(dataset.name, dataset.path(), dataset.latitude_variable or 'lat', dataset.longitude_variable or 'lon')
                    else:
                        logger.info("No new time values found in dataset, nothing to update!")
                except Exception:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    logger.error("Disabling Error: " + repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                finally:
                    nc.close()
                    topo.close()
            else:
                logger.info("Dataset not marked for update ('keep_up_to_date' is False).  Not doing anything.")
        except Exception:
            logger.info("No cache found, Initializing: " + dataset.path())
            create_topology(dataset.name, dataset.path(), dataset.latitude_variable or 'lat', dataset.longitude_variable or 'lon')

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error("Disabling Error: " + repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))


def create_domain_polygon(filename):
    from shapely.geometry import Polygon
    from shapely.ops import cascaded_union

    nc = ncDataset(filename)
    nv = nc.variables['nv'][:, :].T-1
    #print np.max(np.max(nv))
    latn = nc.variables['lat'][:]
    lonn = nc.variables['lon'][:]
    lon = nc.variables['lonc'][:]
    lat = nc.variables['latc'][:]
    #print lat, lon, latn, lonn, nv
    index_pos = numpy.asarray(numpy.where(
        (lat <= 90) & (lat >= -90) &
        (lon <= 180) & (lon > 0),)).squeeze()
    index_neg = numpy.asarray(numpy.where(
        (lat <= 90) & (lat >= -90) &
        (lon < 0) & (lon >= -180),)).squeeze()
    #print np.max(np.max(nv)), np.shape(nv), np.shape(lonn), np.shape(latn)
    if len(index_pos) > 0:
        p = deque()
        p_add = p.append
        for i in index_pos:
            flon, flat = lonn[nv[i, 0]], latn[nv[i, 0]]
            lon1, lat1 = lonn[nv[i, 1]], latn[nv[i, 1]]
            lon2, lat2 = lonn[nv[i, 2]], latn[nv[i, 2]]
            if flon < -90:
                flon = flon + 360
            if lon1 < -90:
                lon1 = lon1 + 360
            if lon2 < -90:
                lon2 = lon2 + 360
            p_add(Polygon(((flon, flat),
                           (lon1, lat1),
                           (lon2, lat2),
                           (flon, flat),)))
        domain_pos = cascaded_union(p)
    if len(index_neg) > 0:
        p = deque()
        p_add = p.append
        for i in index_neg:
            flon, flat = lonn[nv[i, 0]], latn[nv[i, 0]]
            lon1, lat1 = lonn[nv[i, 1]], latn[nv[i, 1]]
            lon2, lat2 = lonn[nv[i, 2]], latn[nv[i, 2]]
            if flon > 90:
                flon = flon - 360
            if lon1 > 90:
                lon1 = lon1 - 360
            if lon2 > 90:
                lon2 = lon2 - 360
            p_add(Polygon(((flon, flat),
                           (lon1, lat1),
                           (lon2, lat2),
                           (flon, flat),)))
        domain_neg = cascaded_union(p)
    if len(index_neg) > 0 and len(index_pos) > 0:
        from shapely.prepared import prep
        domain = prep(cascaded_union((domain_neg, domain_pos,)))
    elif len(index_neg) > 0:
        domain = domain_neg
    elif len(index_pos) > 0:
        domain = domain_pos
    else:
        logger.info(nc.__str__())
        logger.info(lat)
        logger.info(lon)
        logger.error("Domain file creation - No data in topology file Length of positive:%u Length of negative:%u" % (len(index_pos), len(index_neg)))
        raise ValueError("No data in file")

    f = open(filename[:-3] + '.domain', 'w')
    pickle.dump(domain, f)
    f.close()
    nc.close()
