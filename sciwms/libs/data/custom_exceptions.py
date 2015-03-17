'''
Created on Mar 16, 2015

@author: ayan
'''


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