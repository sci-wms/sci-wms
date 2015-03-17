'''
Created on Mar 13, 2015

@author: ayan
'''


def get_nc_variable_values(nc_dataset, var_name):
    try:
        var_values = nc_dataset.variables[var_name][:]
    except KeyError:
        var_values = None
    return var_values


def get_nc_variable(nc_dataset, var_name):
    try:
        var_metadata = nc_dataset.variables[var_name]
    except KeyError:
        var_metadata = None
    return var_metadata