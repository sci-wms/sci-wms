from django.http import HttpResponse
import numpy
#from collections import deque
from StringIO import StringIO
#import fvcom_compute.server_local_config as config
import scipy.io ###
import math

def __main__( actions, u, v, width, height, lonmax, lonmin, latmax, latmin, index, lon, lat, lonn, latn, nv ):

    if "regrid" in actions:
        #size = int(request.GET["size"])
        wid = numpy.max((width, height))
        size = (lonmax - lonmin) / wid
        hi = (latmax - latmin) / size
        hi = math.ceil(hi)
        if "grid" in actions:
            import fvcom_compute.fvcom_stovepipe.regrid as regrid
            
            response = HttpResponse(content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename=fvcom.grd'
            mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
            mag = numpy.sqrt(mag)
            reglon = numpy.linspace(numpy.negative(lonmin), numpy.negative(lonmax), wid)
            reglon = numpy.negative(reglon)
            reglat = numpy.linspace(latmin, latmax, hi)
            
            #buffer = StringIO()
            response.write(('ncols ' + str(len(reglon)) + '\n'))
            response.write(('nrows ' + str(len(reglat)) + '\n'))
            response.write(("xllcenter " + str(lonmin)) + '\n')
            response.write(("yllcenter " + str(latmin)) + '\n')
            response.write(('cellsize ' + str(size) + '\n'))
            response.write(('NODATA_value ' + '-9999\n'))
            
            newvalues = regrid.regrid(mag, lonn, latn, nv, reglon, reglat, size)
        
            #numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
        
            #dat = buffer.getvalue()
            #buffer.close()
            for i,v in enumerate(newvalues):
                response.write(str(v))
                test = float(i) / wid
                if test.is_integer():
                    if i == 0:
                        response.write(" ")
                    else:
                        response.write('\n')
                else: response.write(" ")
                
        else:
            if "nc" in actions:
                response = HttpResponse(content_type='application/netcdf')
                response['Content-Disposition'] = 'attachment; filename=fvcom.nc'
                buffer = StringIO()
                #rootgrp = Dataset(buffer, 'w', clobber=True)
                #level = rootgrp.createDimension('level', 1)
                #time = rootgrp.createDimension('time', 1)
                #index = rootgrp.createDimension('cell', len(u))
                #lonvar = rootgrp.createVariable('lon', 'f8',('cell',))
                #latvar = rootgrp.createVariable('lat', 'f8',('cell',))
                #uvar = rootgrp.createVariable('u','f4',('cell',))
                #vvar = rootgrp.createVariable('v', 'f4',('cell',))
                #magvar = rootgrp.createVariable('mag', 'f4', ('cell',))
                rootgrp = scipy.io.netcdf_file(response, 'w')
                rootgrp.createDimension('cell', len(u))
                lonvar = rootgrp.createVariable('lon', 'f', ('cell',))
                latvar = rootgrp.createVariable('lat', 'f', ('cell',))
                uvar = rootgrp.createVariable('u', 's', ('cell',))
                vvar = rootgrp.createVariable('v', 's', ('cell',))
                magvar = rootgrp.createVariable('velocity', 's', ('cell',))
                
                
                uvar[:] = u
                vvar[:] = v
                latvar[:] = numpy.asarray(lat)
                lonvar[:] = numpy.asarray(lon)
                
                mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                mag = numpy.sqrt(mag)
                magvar[:] = mag
                
                rootgrp.close()
                dat = buffer.getvalue()
                buffer.close()
                response.write(dat)
            elif "text" in actions:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'filename=fvcom.txt'
                X = numpy.asarray([lon,lat,u,v])
                X = numpy.transpose(X)
            
                buffer = StringIO()
            
                numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
            
                dat = buffer.getvalue()
                buffer.close()
                response.write(dat)
                
            elif "mat" in actions:
                response = HttpResponse(content_type='application/matlab-mat')
                response['Content-Disposition'] = 'attachment; filename=fvcom.mat'
                X = numpy.asarray([lon,lat,u,v])
                X = numpy.transpose(X)
            
                buffer = StringIO()
            
                scipy.io.savemat(buffer, { 'data' : X })
                #numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
            
                dat = buffer.getvalue()
                buffer.close()
                response.write(dat)
            elif "shp" in actions:
                import shapefile
                import zipfile
                response = HttpResponse(content_type='application/x-zip')
                response['Content-Disposition'] = 'attachment; filename=fvcom.zip'
                w = shapefile.Writer(shapefile.POLYGON)
                w.field('mag','F')
                mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                mag = numpy.sqrt(mag)
                
                #for i,j in enumerate(lon):
                #    w.point(j, lat[i])
                #    w.record(mag[i])
                for i,v in enumerate(index):
                    w.poly(parts=[[[lonn[nv[i, 0]], latn[nv[i, 0]]], \
                                   [lonn[nv[i, 1]], latn[nv[i, 1]]], \
                                   [lonn[nv[i, 2]], latn[nv[i, 2]]]]])
                    w.record(mag[i])
            
                shp = StringIO()
                shx = StringIO()
                dbf = StringIO()
                w.saveShp(shp)
                w.saveShx(shx)
                w.saveDbf(dbf)
                z = zipfile.ZipFile(response, "w", zipfile.ZIP_STORED)
                z.writestr("fvcom.shp", shp.getvalue())
                z.writestr("fvcom.shx", shx.getvalue())
                z.writestr("fvcom.dbf", dbf.getvalue())
                z.close()
                
    return response