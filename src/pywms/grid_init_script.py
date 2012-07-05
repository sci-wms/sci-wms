'''
Created on Sep 6, 2011

@author: ACrosby
'''
from netCDF4 import Dataset, num2date
import sys
from datetime import datetime
#import pp
import os
import numpy as np


#last_grid_init_path = 'last_grid_init.pywms'


def create_topology(datasetname, url):
    #from netCDF4 import Dataset, num2date
    #import sys
    #from datetime import datetime
    import server_local_config as config
    nc = Dataset(url)
    nclocalpath = os.path.join(config.topologypath, datasetname+".nc")
    #print nclocalpath
    nclocal = Dataset(nclocalpath, mode="w", clobber=True)
    
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
        #time = num2date(times[:], units=times.units)

        #print nclocal.variables['latc'].dtype
        #print nc.variables['latc'].dtype
    
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
    #now = datetime.now()
    #print dir(now)
    #f = open(last_grid_init_path, 'w')
    #f.write(now.__str__())
    #f.close()

    
def create_topology_from_config():
    """
    Initialize topology upon server start up for each of the datasets listed in server_local_config.datasetpath dictionary
    """    
    import server_local_config
    paths = server_local_config.datasetpath #dict
    for dataset in paths.viewkeys():
        print "Adding: " + paths[dataset]
        create_topology(dataset, paths[dataset])


def check_topology_age():
    arrayj = []
    from datetime import datetime

    if True:
        #job_server = pp.Server(2, ppservers=())
        import server_local_config
        from fvcom_stovepipe.parallellock import get_lock, release_lock
        paths = server_local_config.datasetpath #dict
        #print paths
        for dataset in paths.viewkeys():
            #print dataset
            try:
                #get_lock()
                filemtime = datetime.fromtimestamp(
                    os.path.getmtime(
                    os.path.join(
                    server_local_config.topologypath, dataset + ".nc"
                    )))
                #print filemtime
                difference = datetime.now() - filemtime
                if difference.seconds > .5*3600 or difference.days > 0:
                    
                    nc = Dataset(paths[dataset])
                    topo = Dataset(os.path.join(
                        server_local_config.topologypath, dataset + ".nc"))
                        
                    time1 = nc.variables['time'][-1]
                    time2 = topo.variables['time'][-1]
                    
                    nc.close()
                    topo.close()
                    if time1 != time2:    
                        print "Updating: " + paths[dataset]
                        #arrayj.append(job_server.submit(create_topology, (dataset, paths[dataset],),(),("netCDF4","numpy", "datetime")))
                        create_topology(dataset, paths[dataset])
                        #release_lock()
            except:
                print "Initializing: " + paths[dataset]
            ##    #arrayj.append(job_server.submit(create_topology, (dataset, paths[dataset],),(),("netCDF4","numpy", "datetime")))
            #    #get_lock()
                create_topology(dataset, paths[dataset])
            #    #release_lock()
    try:
        nc.close()
        topo.close()
    except:
        pass
    return arrayj
    
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
    






