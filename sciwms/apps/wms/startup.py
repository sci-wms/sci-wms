def run():
    print "Updating datasets..."
    from sciwms.libs.data.caching import update_datasets

    try:
        update_datasets()
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
