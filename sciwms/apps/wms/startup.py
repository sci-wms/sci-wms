def run():
    print "Initializing datasets topologies..."
    from sciwms.libs.data.grid_init_script import init_all_datasets
    init_all_datasets()

    print '\n    ##################################################\n' +\
          '    #                                                #\n' +\
          '    #  Starting sci-wms...                           #\n' +\
          '    #  A wms server for unstructured scientific data #\n' +\
          '    #                                                #\n' +\
          '    ##################################################\n'
