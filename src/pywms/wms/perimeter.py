import numpy
import collections

def get_perimeter( nv ):

    """
    """
    
    #print nv.shape
    #print nv[1:3,:]
    nv  = numpy.vstack((nv.T, nv[:,0].T,)).T
    stack = numpy.vstack((nv[:,0], nv[:,1],))
    print stack.shape
    for i in range(1,nv.shape[1]-1):
        
        stack = numpy.hstack((stack, nv[:,i:i+2].T,))
    print stack.T.shape
    
    #stack = numpy.hstack((stack, numpy.fliplr(stack),))
    
    print stack.T.shape
    #print dir(stack)
    nv_u, nv_nu = unique_items(stack.T)
    #uniq = map(has_all_unique, stack)
    print numpy.asarray(nv_u).shape
    print numpy.asarray(nv_nu).shape
    return nv_u
    
def unique_items(iterable):
    #print iterable
    tuples = map(tuple, iterable)
    #print tuples
    counts = collections.Counter(tuples)
    unique = []
    non_unique = []
    for t in tuples:
        #print t
        if counts[t] == 1:
            unique.append(t)
            #print "unique"
        else:
            print counts[t]
        #    non_unique.append(t)
            #print "nonUnqiue"
            
    return unique, non_unique
            
            
