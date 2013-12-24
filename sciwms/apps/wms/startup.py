def run():
    print "Initializing datasets topologies..."
    from sciwms.libs.data.grid_init_script import init_all_datasets
    try:
        init_all_datasets()
    except BaseException:
        print '\n    ###################################################\n' +\
              '    #                                                 #\n' +\
              '    #  There was a problem initializing some of your  #\n' +\
              '    #  datasets.  Please see the log for more details #\n' +\
              '    #                                                 #\n' +\
              '    ###################################################\n'

    print '\n    ##################################################\n' +\
          '    #                                                #\n' +\
          '    #  Starting sci-wms...                           #\n' +\
          '    #  A wms server for unstructured scientific data #\n' +\
          '    #                                                #\n' +\
          '    ##################################################\n'
