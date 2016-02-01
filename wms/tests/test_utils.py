'''
Created on Jul 21, 2015

@author: ayan
'''
import unittest
import numpy as np

from ..utils import (adjacent_array_value_differences, calc_safety_factor,
                     calc_lon_lat_padding)


class TestAdjacentArrayValueDifferences(unittest.TestCase):

    def setUp(self):
        self.test_data = [(1.5, 3, 4, 6.5),
                          (2.3, 4.5, 9.6, 10)
                          ]
        self.test_array = np.array(self.test_data)

    def test_adj_arr_diff(self):
        result = adjacent_array_value_differences(self.test_array)
        expected_data = [(-1.5, -1, -2.5),
                         (-2.2, -5.1, -0.4)
                         ]
        expected_array = np.array(expected_data)
        np.testing.assert_almost_equal(result, expected_array, decimal=2)


class TestCalcSafetyFactor(unittest.TestCase):

    def setUp(self):
        self.low_value = 0.5
        self.high_value = 1000

    def test_calc_with_low_value(self):
        result = calc_safety_factor(self.low_value)
        expected = 2195.6896
        self.assertAlmostEqual(result, expected, 3)

    def test_calc_with_high_value(self):
        result = calc_safety_factor(self.high_value)
        expected = 10
        self.assertEqual(result, expected)


class TestCalcLonLatPadding(unittest.TestCase):

    def setUp(self):
        self.lon_data = [(-74.5, -75.0, -75.5, -76.0),
                         (-74.3, -74.8, -75.3, -75.8)
                         ]
        self.lat_data_small = [(14.2, 14.4, 14.6, 14.8),
                               (14.3, 14.5, 14.7, 14.9)
                               ]
        self.lat_data_large = [(14.1, 14.7, 15.3, 15.9),
                               (15.2, 15.8, 16.4, 17.0)
                               ]
        self.lon_array = np.array(self.lon_data)
        self.lat_array_small = np.array(self.lat_data_small)
        self.lat_array_large = np.array(self.lat_data_large)

    def test_large_lon_delta(self):
        result = calc_lon_lat_padding(self.lon_array, self.lat_array_small)
        expected = 5.0
        self.assertAlmostEqual(result, expected, 3)

    def test_large_lat_delta(self):
        result = calc_lon_lat_padding(self.lon_array, self.lat_array_large)
        expected = 11
        self.assertAlmostEqual(result, expected, 3)
