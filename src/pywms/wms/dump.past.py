"""
                        elif "flow" in actions:
                            #fig.set_figheight(height/80.0)
                            #fig.set_figwidth(width/80.0)
                            if topology_type.lower() == "cell":
                                lon, lat = lon, lat
                                lonn, latn = lonn, latn
                            else:
                                lon, lat = lonn, latn
                                lonn, latn = lon, lat

                            if lonmax-lonmin < 3:
                                num = 300
                            elif lonmax-lonmin < 5:
                                num = 500
                            elif lonmax-lonmin < 9:
                                num = 900
                            else:
                                num = 2500

                            xi = numpy.arange(lonmin, lonmax, num)
                            yi = numpy.arange(latmin, latmax, num)

                            from matplotlib.mlab import griddata

                            f = open(os.path.join(config.topologypath, dataset + '.domain'))
                            domain = pickle.load(f)
                            f.close()
                            import shapely.geometry

                            if topology_type.lower() == "node":
                                n = numpy.unique(nv)
                                u = griddata(lon[n], lat[n], var1[n], xi, yi, interp='nn')
                                v = griddata(lon[n], lat[n], var2[n], xi, yi, interp='nn')
                            else:
                                u = griddata(lon, lat, var1, xi, yi, interp='nn')
                                v = griddata(lon, lat, var2, xi, yi, interp='nn')
                            xi = xi.flatten()
                            yi = yi.flatten()
                            cont = domain.overlaps(shapely.geometry.MultiPoint(numpy.asarray((xi,yi)).T))

                            u.flatten()[cont==False] = 0
                            v.flatten()[cont==False] = 0

                            import seeded_flow
                            js = seeded_flow.js_container(xi,yi,u,v)
                            #html = seeded_flow.html5_canvas(js)
                            dataresponse = HttpResponse(content_type='application/json')
                            dataresponse.write(js)

                        elif "shape" in actions:
                            import shapefile
                            import zipfile
                            dataresponse = HttpResponse(content_type='application/x-zip')
                            dataresponse['Content-Disposition'] = 'attachment; filename=fvcom.zip'
                            w = shapefile.Writer(shapefile.POLYGON)
                            w.field('mag','F')
                            mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)
                            mag = numpy.sqrt(mag)

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
                            z = zipfile.ZipFile(dataresponse, "w", zipfile.ZIP_STORED)
                            #z = zipfile.ZipFile('/home/acrosby/alexsfvcomshape.zip', 'w', zipfile.ZIP_STORED)
                            z.writestr("fvcom.shp", shp.getvalue())
                            z.writestr("fvcom.shx", shx.getvalue())
                            z.writestr("fvcom.dbf", dbf.getvalue())
                            z.close()
                        """

                        """
                elif "data" in actions:
                    if "regrid" in actions:
                        #size = int(request.GET["size"])
                        wid = numpy.max((width, height))
                        size = (lonmax - lonmin) / wid
                        hi = (latmax - latmin) / size
                        hi = math.ceil(hi)
                        if "grid" in actions:
                            import pywms.wms.regrid as regrid

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
                            mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)
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
                            #z = zipfile.ZipFile(response, "w", zipfile.ZIP_STORED)
                            z = zipfile.ZipFile('/home/acrosby/alexsfvcomshape.zip', 'w', zipfile.ZIP_STORED)
                            z.writestr("fvcom.shp", shp.getvalue())
                            z.writestr("fvcom.shx", shx.getvalue())
                            z.writestr("fvcom.dbf", dbf.getvalue())
                            z.close()
                """