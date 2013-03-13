'''
Created on Sep 6, 2011

@author: ACrosby

!!!THIS IS NOT A SCRIPT ANYMORE!!!
'''
from dateutil.parser import parse
from netCDF4 import Dataset as ncDataset
from netCDF4 import num2date, date2num
import sys, os, numpy, logging, traceback
from datetime import datetime
import numpy as np
from pywms.wms.models import Dataset
from pywms import build_tree
import server_local_config as config
import multiprocessing
from collections import deque
import shutil
try:
    import cPickle as pickle
except:
    import Pickle as pickle

s = multiprocessing.Semaphore(1)

output_path = os.path.join(config.fullpath_to_wms, 'src', 'pywms', 'sciwms_wms')
# Set up Logger
logger = multiprocessing.get_logger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler('%s.log' % output_path)
formatter = logging.Formatter(fmt='[%(asctime)s] - <<%(levelname)s>> - |%(message)s|')
handler.setFormatter(formatter)
logger.addHandler(handler)

time_units = 'hours since 1970-01-01'

def create_topology(datasetname, url):
    try:
        nc = ncDataset(url)
        nclocalpath = os.path.join(config.topologypath, datasetname+".nc.updating")
        nclocal = ncDataset(nclocalpath, mode="w", clobber=True)
        if nc.variables.has_key("nv"):
            logger.info("identified as fvcom")
            grid = 'False'

            nclocal.createDimension('cell', nc.variables['latc'].shape[0])#90415)
            nclocal.createDimension('node', nc.variables['lat'].shape[0])
            nclocal.createDimension('time', nc.variables['time'].shape[0])
            nclocal.createDimension('corners', nc.variables['nv'].shape[0])

            lat = nclocal.createVariable('lat', 'f', ('node',), chunksizes=nc.variables['lat'].shape, zlib=False, complevel=0)
            lon = nclocal.createVariable('lon', 'f', ('node',), chunksizes=nc.variables['lat'].shape, zlib=False, complevel=0)
            latc = nclocal.createVariable('latc', 'f', ('cell',), chunksizes=nc.variables['latc'].shape, zlib=False, complevel=0)
            lonc = nclocal.createVariable('lonc', 'f', ('cell',), chunksizes=nc.variables['latc'].shape, zlib=False, complevel=0)
            nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=nc.variables['nv'].shape, zlib=False, complevel=0)

            time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=nc.variables['time'].shape, zlib=False, complevel=0) #d
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

            nv[:,:] = nc.variables['nv'][:,:]
            logger.info("done filling vars")
            # DECODE the FVCOM datetime string (Time) and save as a high precision datenum
            timestrs = nc.variables['Times'][:] #format: "2013-01-15T00:00:00.000000"
            dates = [datetime.strptime(timestrs[i, :].tostring(), "%Y-%m-%dT%H:%M:%S.%f") for i in range(len(timestrs[:,0]))]
            time[:] = date2num(dates, units=time_units)# use netCDF4's date2num function
            #time[:] = nc.variables['time'][:]
            logger.info("done time conversion")
            time.units = time_units
            #time.units = nc.variables['time'].units
            nclocal.sync()
            nclocal.grid = grid
            nclocal.sync()
            logger.info("data written to file")

        elif nc.variables.has_key("element"):
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
                                    nc.variables['element'][:,:]-1
                                    )

            lonc[:] = lontemp[tri.triangles].mean(axis=1)
            latc[:] = lattemp[tri.triangles].mean(axis=1)
            nv[:,:] = nc.variables['element'][:,:].T
            time[:] = nc.variables['time'][:]
            time.units = nc.variables['time'].units
            nclocal.sync()
            nclocal.grid = grid
            nclocal.sync()
            logger.info("data written to file")

        else:
            logger.info("identified as grid")
            #print str(nc.variables['lat'].ndim)
            latname, lonname = 'lat', 'lon'
            if latname not in nc.variables:
                for key in nc.variables.iterkeys():
                    try:
                        nc.variables[key].__getattr__('units')
                        temp_units = nc.variables[key].units
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
            latchunk, lonchunk = (igrid,jgrid,), (igrid,jgrid,)
            logger.info("native grid style identified")
            nclocal.createDimension('igrid', igrid)
            nclocal.createDimension('jgrid', jgrid)
            nclocal.createDimension('time', nc.variables['time'].shape[0])

            lat = nclocal.createVariable('lat', 'f', ('igrid','jgrid',), chunksizes=latchunk, zlib=False, complevel=0)
            lon = nclocal.createVariable('lon', 'f', ('igrid','jgrid',), chunksizes=lonchunk, zlib=False, complevel=0)
            if nc.variables['time'].ndim > 1:
                time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=(nc.variables['time'].shape[0],), zlib=False, complevel=0)
            else:
                time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=nc.variables['time'].shape, zlib=False, complevel=0)
            logger.info("variables created in cache")
            lontemp = nc.variables[lonname][:]
            lontemp[lontemp > 180] = lontemp[lontemp > 180] - 360

            if grid == 'rgrid':
                lon[:], lat[:] = np.meshgrid(lontemp, nc.variables[latname][:])
                grid = 'cgrid'
            else:
                lon[:] = lontemp
                lat[:] = nc.variables[latname][:]
            if nc.variables['time'].ndim > 1:
                _str_data = nc.variables['time'][:,:]
                #print _str_data.shape, type(_str_data), "''", str(_str_data[0,:].tostring().replace(" ","")), "''"
                dates = [parse(_str_data[i, :].tostring()) for i in range(len(_str_data[:,0]))]
                time[:] = date2num(dates, time_units)
                time.units = time_units
            else:
                time[:] = nc.variables['time'][:]
                time.units = nc.variables['time'].units
            logger.info("data written to file")
            while not 'grid' in nclocal.ncattrs():
                nclocal.__setattr__('grid', 'cgrid')
                nclocal.sync()
        nclocal.sync()
        nclocal.close()
        nc.close()
        shutil.move(nclocalpath, nclocalpath.replace(".updating", ""))
        if not (os.path.exists(nclocalpath.replace(".updating", "").replace(".nc",'_nodes.dat')) and os.path.exists(nclocalpath.replace(".updating", "").replace(".nc","_nodes.idx"))):
            build_tree.build_from_nc(nclocalpath.replace(".updating", ""))
        if grid == 'False':
            if not os.path.exists(nclocalpath.replace(".updating", "")[:-3] + '.domain'):
                create_domain_polygon(nclocalpath.replace(".updating", ""))

    except Exception as detail:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error("Disabling Error: " +\
                                 repr(traceback.format_exception(exc_type, exc_value,
                                              exc_traceback)))
        os.unlink(nclocalpath)

def create_topology_from_config():
    """
    Initialize topology upon server start up for each of the datasets listed in server_local_config.datasetpath dictionary
    """
    datasets = Dataset.objects.values()
    for dataset in datasets:
        print "Adding: " + dataset["name"]
        create_topology(dataset["name"], dataset["uri"])


def check_topology_age():
    try:
        from datetime import datetime
        if True:
            datasets = Dataset.objects.values()
            jobs = []
            for dataset in datasets:
                #print dataset
                name = dataset["name"]
                p = multiprocessing.Process(target=do, args=(name,dataset,s))
                p.daemon = True
                p.start()
                jobs.append(p)
                #do(name, dataset)
    except Exception as detail:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error("Disabling Error: " +\
                                 repr(traceback.format_exception(exc_type, exc_value,
                                              exc_traceback)))
def do(name, dataset, s):
    with s:
        try:
            try:
                #get_lock()
                filemtime = datetime.fromtimestamp(
                    os.path.getmtime(
                    os.path.join(
                    config.topologypath, name + ".nc"
                    )))
                #print filemtime
                difference = datetime.now() - filemtime
                if dataset["keep_up_to_date"]:
                    if difference.seconds > .5*3600 or difference.days > 0:
                        #print "true"
                        nc = ncDataset(dataset["uri"])
                        topo = ncDataset(os.path.join(
                            config.topologypath, name + ".nc"))

                        time1 = nc.variables['time'][-1]
                        time2 = topo.variables['time'][-1]
                        #print time1, time2
                        nc.close()
                        topo.close()
                        if time1 != time2:
                            check = True
                            logger.info("Updating: " + dataset["uri"])
                            create_topology(name, dataset["uri"])
                            #while check:
                            #    try:
                            #        check_nc = ncDataset(nclocalpath)
                            #        check_nc.close()
                            #        check = False
                            #    except: # TODO: Catch the specific file corrupt error im looking for here
                            #        create_topology(name, dataset["uri"])
            except:
                logger.info("Initializing: " + dataset["uri"])
                create_topology(name, dataset["uri"])
            try:
                nc.close()
                topo.close()
            except:
                pass
        except Exception as detail:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error("Disabling Error: " +\
                                 repr(traceback.format_exception(exc_type, exc_value,
                                              exc_traceback)))

def create_domain_polygon(filename):
    from shapely.geometry import Polygon
    from shapely.ops import cascaded_union

    #from shapely.prepared import prep

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
            flon, flat = lonn[nv[i,0]], latn[nv[i,0]]
            lon1, lat1 = lonn[nv[i,1]], latn[nv[i,1]]
            lon2, lat2 = lonn[nv[i,2]], latn[nv[i,2]]
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
            flon, flat = lonn[nv[i,0]], latn[nv[i,0]]
            lon1, lat1 = lonn[nv[i,1]], latn[nv[i,1]]
            lon2, lat2 = lonn[nv[i,2]], latn[nv[i,2]]
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
        domain = prep(cascaded_union((domain_neg, domain_pos,)))
    elif len(index_neg) > 0:
        domain = domain_neg
    elif len(index_pos) > 0:
        domain = domain_pos
    else:
        logger.info(nc.__str__())
        logger.error("Domain file creation - No data in topology file")
        raise ValueError("No data in file")

    f = open(filename[:-3] + '.domain', 'w')
    pickle.dump(domain, f)
    f.close()
    nc.close()






