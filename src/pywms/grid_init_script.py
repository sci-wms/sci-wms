'''
Created on Sep 6, 2011

@author: ACrosby
'''
from netCDF4 import Dataset as ncDataset
from netCDF4 import num2date
import sys
from datetime import datetime
import os
import numpy as np
from pywms.wms.models import Dataset
import server_local_config
import multiprocessing
from collections import deque
import pickle

def create_topology(datasetname, url):
    import server_local_config as config
    nc = ncDataset(url)
    nclocalpath = os.path.join(config.topologypath, datasetname+".nc")
    nclocal = ncDataset(nclocalpath, mode="w", clobber=True)
    
    if nc.variables.has_key("nv"):
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
        
        lontemp = nc.variables['lon'][:]
        if np.max(lontemp) > 180:
            #print "greaterthan"
            lonctemp = nc.variables['lonc'][:]
            lontemp[lontemp > 180] = lontemp[lontemp > 180] - 360
            lonctemp[lonctemp > 180] = lonctemp[lonctemp > 180] -360
            lon[:] = np.asarray(lontemp)
            lonc[:] = np.asarray(lonctemp)
        #elif np.min(lontemp) < -180:
        #    print "lessthan"
        #    lon[:] = np.asarray(lontemp) + 360
        #    lonc[:] = np.asarray(nc.variables['lonc'][:] + 360)
        else:
        #    print "nochange"
            lon[:] = lontemp
            lonc[:] = nc.variables['lonc'][:]
                
        lat[:] = nc.variables['lat'][:]
        latc[:] = nc.variables['latc'][:]
        
        nv[:,:] = nc.variables['nv'][:,:]
        time[:] = nc.variables['time'][:]
        time.units = nc.variables['time'].units
    
    elif nc.variables.has_key("element"):
        nclocal.createDimension('node', nc.variables['x'].shape[0])
        nclocal.createDimension('cell', nc.variables['element'].shape[0])
        nclocal.createDimension('time', nc.variables['time'].shape[0])
        nclocal.createDimension('corners', nc.variables['element'].shape[1])

        lat = nclocal.createVariable('lat', 'f', ('node',), chunksizes=(nc.variables['x'].shape[0],), zlib=False, complevel=0)
        lon = nclocal.createVariable('lon', 'f', ('node',), chunksizes=(nc.variables['x'].shape[0],), zlib=False, complevel=0)
        latc = nclocal.createVariable('latc', 'f', ('cell',), chunksizes=(nc.variables['element'].shape[0],), zlib=False, complevel=0)
        lonc = nclocal.createVariable('lonc', 'f', ('cell',), chunksizes=(nc.variables['element'].shape[0],), zlib=False, complevel=0)
        nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=nc.variables['element'].shape[::-1], zlib=False, complevel=0)

        time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=nc.variables['time'].shape, zlib=False, complevel=0) 
        
        lattemp = nc.variables['y'][:]
        lontemp = nc.variables['x'][:]
        lat[:] = lattemp
        if max(lontemp) > 180:
            lontemp = np.asarray(lontemp) - 360
        
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
    nclocal.close()
    nc.close()
    create_domain_polygon(nclocalpath)

def create_topology_from_config():
    """
    Initialize topology upon server start up for each of the datasets listed in server_local_config.datasetpath dictionary
    """    
    datasets = Dataset.objects.values()
    for dataset in datasets:
        print "Adding: " + dataset["name"]
        create_topology(dataset["name"], dataset["uri"])


def check_topology_age():
    from datetime import datetime
    if True:
        datasets = Dataset.objects.values()
        jobs = []
        for dataset in datasets:
            #print dataset
            name = dataset["name"]
            p = multiprocessing.Process(target=do, args=(name,dataset,))
            p.start()
            jobs.append(p)
    
def do(name, dataset):
    try:
        try:
            #get_lock()
            filemtime = datetime.fromtimestamp(
                os.path.getmtime(
                os.path.join(
                server_local_config.topologypath, name + ".nc"
                )))
            #print filemtime
            difference = datetime.now() - filemtime
            if dataset["keep_up_to_date"]:
                if difference.seconds > .5*3600 or difference.days > 0:
                    
                    nc = ncDataset(dataset["uri"])
                    topo = ncDataset(os.path.join(
                        server_local_config.topologypath, name + ".nc"))
                        
                    time1 = nc.variables['time'][-1]
                    time2 = topo.variables['time'][-1]
                    
                    nc.close()
                    topo.close()
                    if time1 != time2:    
                        print "Updating: " + dataset["uri"]
                        create_topology(name, dataset["uri"])

        except:
            print "Initializing: " + dataset["uri"]
            create_topology(name, dataset["uri"])
        try:
            nc.close()
            topo.close()
        except:
            pass
    except:
        pass
    
def create_domain_polygon(filename):
    from shapely.geometry import Polygon
    from shapely.ops import cascaded_union
    nc = ncDataset(filename)
    nv = nc.variables['nv'][:, :].T-1
    latn = nc.variables['lat'][:]
    lonn = nc.variables['lon'][:]
    p = deque()
    p_add = p.append
    for i in range(len(nv[:,0])):
            flon, flat = lonn[nv[i,0]], latn[nv[i,0]]
            p_add(Polygon(((flon, flat),
                          (lonn[nv[i,1]], latn[nv[i,1]]),
                          (lonn[nv[i,2]], latn[nv[i,2]]),
                          (flon, flat),)))
    #p = [Polygon((lonn[nv[i,0]], latn[nv[i,0]]),
    #             (lonn[nv[i,1]], latn[nv[i,1]]),
    #             (lonn[nv[i,2]], latn[nv[i,2]]),
    #             (lonn[nv[i,0]], latn[nv[i,0]]))]
    domain = cascaded_union(p)
    f = open(filename[:-3] + '.domain', 'w')
    pickle.dump(domain, f)
    f.close()
    nc.close()
    
if __name__ == '__main__':
    """
    Initialize topology upon server start up for each of the datasets listed in server_local_config.datasetpath dictionary
       
    import server_local_config

    paths = server_local_config.datasetpath #dict
    for dataset in paths.viewkeys():
        print "Adding: " + paths[dataset]
        create_topology(dataset, paths[dataset])
    """
    create_topology_from_config()
    






