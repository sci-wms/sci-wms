'''
Created on Mar 13, 2015

@author: ayan
'''
import numpy as np


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


def create_nan_mask(np_arr):
    arr_nans = np.isnan(np_arr)
    nan_mask = np.logical_not(arr_nans)
    return nan_mask


def filter_array(np_arr, mask_arr):
    filtered_arr = np_arr[mask_arr]
    return filtered_arr
    