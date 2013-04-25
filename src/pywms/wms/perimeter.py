'''
COPYRIGHT 2010 Alexander Crosby

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.
'''

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
            
            
