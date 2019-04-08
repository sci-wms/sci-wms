'''
Created on Aug 28, 2015

@author: ayan
'''
import datetime

import pyproj

from django.test import TestCase
from django.test.client import RequestFactory

from ..wms_handler import get_time, get_projection


class TestGetTime(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_time_with_offset(self):
        request = self.factory.get('/dataset?time=2015-01-01T15%3A00%3A00-05%3A00')
        result_time = get_time(request)
        result_time_tz = result_time.tzinfo
        expected_dt = datetime.datetime(2015, 1, 1, 20, 0, 0)
        self.assertEqual(result_time, expected_dt)
        self.assertIsNone(result_time_tz)

    def test_get_time_without_tz(self):
        request = self.factory.get('/dataset?time=2015-01-01T16%3A00%3A00')
        result_time = get_time(request)
        result_time_tz = result_time.tzinfo
        expected_dt = datetime.datetime(2015, 1, 1, 16, 0, 0)
        self.assertEqual(result_time, expected_dt)
        self.assertIsNone(result_time_tz)

    def test_get_time_wms_spec(self):
        request = self.factory.get('/dataset?time=2015-01-01T17%3A00%3A00Z')  # include the "Z" suffix
        result_time = get_time(request)
        result_time_tz = result_time.tzinfo
        expected_dt = datetime.datetime(2015, 1, 1, 17, 0, 0)
        self.assertEqual(result_time, expected_dt)
        self.assertIsNone(result_time_tz)


class TestGetProjection(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_projection_default(self):
        # CRS
        request = self.factory.get('/dataset?crs=EPSG:3857')
        result_proj = get_projection(request)
        self.assertEqual(
            result_proj.definition_string(),
            pyproj.Proj(init='EPSG:3857').definition_string()
        )

        # SRS
        request = self.factory.get('/dataset?srs=epsg:3857')
        result_proj = get_projection(request)
        self.assertEqual(
            result_proj.definition_string(),
            pyproj.Proj(init='EPSG:3857').definition_string()
        )

        # Fallback to the default
        request = self.factory.get('/dataset?nothing=epsg:3857')
        result_proj = get_projection(request)
        self.assertEqual(
            result_proj.definition_string(),
            pyproj.Proj(init='EPSG:3857').definition_string()
        )
