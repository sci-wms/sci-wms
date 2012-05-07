timevalsqs = Time.objects.filter(date__gte=datestart).filter(date__lte=dateend).values("date")
            timevals = map(getVals, timevalsqs, numpy.ones(len(timesqs))*4)
            
            if "image" in actions:
                fig = Plot.figure()
                fig.set_alpha(0)
                ax = fig.add_subplot(111)

                #for direction in ["left", "right", "bottom", "top"]:
                #ax.set_frame_on(False)
                #ax.set_clip_on(False)
                #ax.set_position([0,0,1,1])
                #Plot.yticks(visible=False)
                #Plot.xticks(visible=False)
            
                #ax.set_xlim()
                #ax.set_ylim()
                
                canvas = Plot.get_current_fig_manager().canvas
            
                response = HttpResponse(content_type='image/png')
                canvas.print_png(response)
            elif "data" in actions:
                if "nc" in actions:
                    pass
                elif "text" in actions:
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'filename=fvcom.txt'
                    X = numpy.asarray((u,v))
                    X = numpy.transpose(X)
              
                    buffer = StringIO()
        
                    numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
        
                    dat = buffer.getvalue()
                    buffer.close()
                    response.write(dat)
                elif "mat" in actions:
                    response = HttpResponse(content_type='application/matlab-mat')
                    response['Content-Disposition'] = 'attachment; filename=fvcom.mat'
                    X = numpy.asarray((u,v))
                    X = numpy.transpose(X)
              
                    buffer = StringIO()
        
                    scipy.io.savemat(buffer, { 'data' : X })
                    #numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
        
                    dat = buffer.getvalue()
                    buffer.close()
                    response.write(dat)