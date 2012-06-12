'''
Created on Sep 6, 2011

@author: ACrosby
'''

from netCDF4 import Dataset, num2date
import sys
#url = "http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3"
url = sys.argv[1]
#url = dapdata
nc = Dataset(url)
nclocal = Dataset("topology.nc", "w")

nclocal.createDimension('cell', nc.variables['latc'].shape[0])#90415)
nclocal.createDimension('node', nc.variables['lat'].shape[0])
nclocal.createDimension('time', nc.variables['time'].shape[0])
nclocal.createDimension('corners', nc.variables['nv'].shape[0])

lat = nclocal.createVariable('lat', 'f', ('node',), chunksizes=nc.variables['lat'].shape, zlib=False, complevel=0)
lon = nclocal.createVariable('lon', 'f', ('node',), chunksizes=nc.variables['lat'].shape, zlib=False, complevel=0)
latc = nclocal.createVariable('latc', 'f', ('cell',), chunksizes=nc.variables['latc'].shape, zlib=False, complevel=0)
lonc = nclocal.createVariable('lonc', 'f', ('cell',), chunksizes=nc.variables['latc'].shape, zlib=False, complevel=0)
nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=nc.variables['nv'].shape, zlib=False, complevel=0)

time = nclocal.createVariable('time', 'f8', ('time',), chunksizes=nc.variables['time'].shape, zlib=False, complevel=0) 

lat[:] = nc.variables['lat'][:]
lon[:] = nc.variables['lon'][:]
latc[:] = nc.variables['latc'][:]
lonc[:] = nc.variables['lonc'][:]
nv[:,:] = nc.variables['nv'][:,:]
time[:] = nc.variables['time'][:]
time.units = nc.variables['time'].units
#time = num2date(times[:], units=times.units)

#print nclocal.variables['latc'].dtype
#print nc.variables['latc'].dtype


nclocal.sync()




    
    
