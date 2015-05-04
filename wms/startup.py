def run():
    print "Updating datasets..."
    from django.apps import apps
    Dataset = apps.get_model('wms.Dataset')
    print "Updating datasets..."
    for d in Dataset.objects.all():
        print "Updating {}".format(d.name),
        try:
            d.update_cache()
            print "... done"
        except NotImplementedError:
            print "... not supported!"

    print '\n    ##################################################\n' +\
          '    #                                                #\n' +\
          '    #  Starting sci-wms...                           #\n' +\
          '    #  A wms server for unstructured scientific data #\n' +\
          '    #                                                #\n' +\
          '    ##################################################\n'
