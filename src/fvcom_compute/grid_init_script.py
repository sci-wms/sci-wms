'''
Created on Sep 6, 2011

@author: ACrosby
'''

from netCDF4 import Dataset, num2date

url = "http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3"
#url = dapdata
nc = Dataset(url)
nclocal = Dataset("topology.nc", "w")

nclocal.createDimension('cell', 90415)
nclocal.createDimension('node', 48451)
nclocal.createDimension('time', None)
nclocal.createDimension('corners', 3)

lat = nclocal.createVariable('lat', 'f', ('node',), chunksizes=(48451,), zlib=False, complevel=0)
lon = nclocal.createVariable('lon', 'f', ('node',), chunksizes=(48451,), zlib=False, complevel=0)
latc = nclocal.createVariable('latc', 'f', ('cell',), chunksizes=(90415,), zlib=False, complevel=0)
lonc = nclocal.createVariable('lonc', 'f', ('cell',), chunksizes=(90415,), zlib=False, complevel=0)
nv = nclocal.createVariable('nv', 'u8', ('corners', 'cell',), chunksizes=(3, 90415,), zlib=False, complevel=0)

time = nclocal.createVariable('time', 'f8', ('time',)) 

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




    
    
