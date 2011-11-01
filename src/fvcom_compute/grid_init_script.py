'''
Created on Sep 6, 2011

@author: ACrosby
'''
from fvcom_compute.fvcom_stovepipe.models import Node, Cell, Time
from netCDF4 import Dataset, num2date
#import datetime
#import win32com.client
#import numpy
url = "http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3"
nc = Dataset(url)
lat = nc.variables['lat'][:]
lon = nc.variables['lon'][:]
latc = nc.variables['latc'][:]
lonc = nc.variables['lonc'][:]
nv = nc.variables['nv'][:,:]
times = nc.variables['time']
time = num2date(times[:], units=times.units)


#matlab = win32com.client.Dispatch("matlab.application")
#matlab.Execute('''
#nc = cfdataset('http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3');
#time = nc.time('time');
#time = datevec(time);
#''')
#time = matlab.GetVariable("time", "base")


for i,d in enumerate(time):
    #d = datetime.datetime(int(time[i][0]), int(time[i][1]), int(time[i][2]),\
    #    int(time[i][3]), int(time[i][4]), int(time[i][5]))
    t = Time(date=d, index=i+1)
    t.save()

for i in range(len(lat)):
    n = Node(index=i+1, lat=lat[i], lon=lon[i])
    n.save()
    
for i in range(len(latc)):
    c = Cell(index=i+1, lat=latc[i], lon=lonc[i], node1=nv[0, i], node2=nv[1, i], node3=nv[2, i])
    c.save()


    
    