'''
Created on Mar 16, 2015

@author: ayan
'''
import warnings
import functools


class NonCompliantDataset(Exception):
    
    base_message = 'The {0} dataset found at {1} appears to be neither UGRID nor SGRID compliant.'
    
    def __init__(self, dataset_name, dataset_url):
        self.dataset_name = dataset_name
        self.dataset_url = dataset_url
        
    def __str__(self):
        exception_message = self.base_message.format(self.dataset_name, 
                                                     self.dataset_url
                                                     )
        return exception_message
    
    
def deprecated(deprecated_function):
    @functools.wraps(deprecated_function)
    def new_func(*args, **kwargs):
        warnings.warn_explicit('Call to deprecated function: {0}'.format(deprecated_function.__name__),
                               category=DeprecationWarning,
                               filename=deprecated_function.func_code.co_filename,
                               lineno=deprecated_function.func_code.co_firstlineno + 1
                               )
        return deprecated_function(*args, **kwargs)
    return new_func