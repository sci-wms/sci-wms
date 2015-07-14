# -*- coding: utf-8 -*-
from copy import copy

from django.test import TestCase
from wms.tests import *
from wms.models import Dataset

from sciwms import logger


class TestUgridLegendGraphic(TestCase):

    @classmethod
    def setUpClass(cls):
        add_server()
        add_group()
        add_user()
        add_dataset("ugrid_legend_testing", "ugrid", "selfe_ugrid.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(slug="ugrid_legend_testing")
        d.clear_cache()
        d.delete()

    def setUp(self):
        self.dataset_slug = 'ugrid_legend_testing'
        self.url_params = dict(
            request = 'GetLegendGraphic',
            layer   = 'surface_salt',
            format  = 'image/png',
            width   = 100,
            height  = 300,
            colorscalerange='1,50',
            style='pcolor_jet'
        )

    def image_name(self, fmt):
        return '{}.{}'.format(self.id().split('.')[-1], fmt)

    def do_test(self, params, fmt=None, write=True):
        fmt = fmt or 'png'
        response = self.client.get('/wms/datasets/{}'.format(self.dataset_slug), params)
        self.assertEqual(response.status_code, 200)
        outfile = image_path(self.__class__.__name__, self.image_name(fmt))
        if write is True:
            with open(outfile, "wb") as f:
                f.write(response.content)
        return outfile

    def test_ugrid_legend_pcolor(self):
        params = copy(self.url_params)
        self.do_test(params)

    def test_ugrid_legend_pcolor_logscale(self):
        params = copy(self.url_params)
        params.update(logscale='true')
        self.do_test(params)

    def test_ugrid_legend_pcolor_horizontal(self):
        params = copy(self.url_params)
        params.update(horizontal='true', width=500, height=100)
        self.do_test(params)

    def test_ugrid_legend_pcolor_no_label(self):
        params = copy(self.url_params)
        params.update(showlabel='false')
        self.do_test(params)

    def test_ugrid_legend_pcolor_no_values(self):
        params = copy(self.url_params)
        params.update(showvalues='false')
        self.do_test(params)

    def test_ugrid_legend_pcolor_no_values_no_label(self):
        params = copy(self.url_params)
        params.update(showvalues='false', showlabel='false')
        self.do_test(params)

    def test_ugrid_legend_pcolor_custom_units(self):
        params = copy(self.url_params)
        params.update(unitlabel='somethingelse')
        self.do_test(params)

    def test_ugrid_legend_filledcontours(self):
        params = copy(self.url_params)
        params.update(style='filledcontours_jet')
        self.do_test(params)

    def test_ugrid_legend_contours(self):
        params = copy(self.url_params)
        params.update(style='contours_jet')
        self.do_test(params)

    def test_ugrid_legend_contours_horizontal(self):
        params = copy(self.url_params)
        params.update(style='contours_jet', horizontal='true', width=500, height=100)
        self.do_test(params)


class TestSgridLegendGraphic(TestCase):

    @classmethod
    def setUpClass(cls):
        add_server()
        add_group()
        add_user()
        add_dataset("sgrid_legend_testing", "sgrid", "coawst_sgrid.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(slug="sgrid_legend_testing")
        d.clear_cache()
        d.delete()

    def setUp(self):
        self.dataset_slug = 'sgrid_legend_testing'
        self.url_params = dict(
            request = 'GetLegendGraphic',
            layer   = 'u',
            format  = 'image/png',
            width   = 100,
            height  = 300,
            colorscalerange='1,50',
            style='pcolor_jet'
        )

    def image_name(self, fmt):
        return '{}.{}'.format(self.id().split('.')[-1], fmt)

    def do_test(self, params, fmt=None, write=True):
        fmt = fmt or 'png'
        response = self.client.get('/wms/datasets/{}'.format(self.dataset_slug), params)
        self.assertEqual(response.status_code, 200)
        outfile = image_path(self.__class__.__name__, self.image_name(fmt))
        if write is True:
            with open(outfile, "wb") as f:
                f.write(response.content)
        return outfile

    def test_sgrid_legend_pcolor(self):
        params = copy(self.url_params)
        self.do_test(params)

    def test_sgrid_legend_pcolor_logscale(self):
        params = copy(self.url_params)
        params.update(logscale='true')
        self.do_test(params)

    def test_sgrid_legend_pcolor_horizontal(self):
        params = copy(self.url_params)
        params.update(horizontal='true', width=500, height=100)
        self.do_test(params)

    def test_sgrid_legend_pcolor_no_label(self):
        params = copy(self.url_params)
        params.update(showlabel='false')
        self.do_test(params)

    def test_sgrid_legend_pcolor_no_values(self):
        params = copy(self.url_params)
        params.update(showvalues='false')
        self.do_test(params)

    def test_sgrid_legend_pcolor_no_values_no_label(self):
        params = copy(self.url_params)
        params.update(showvalues='false', showlabel='false')
        self.do_test(params)

    def test_sgrid_legend_pcolor_custom_units(self):
        params = copy(self.url_params)
        params.update(unitlabel='somethingelse')
        self.do_test(params)

    def test_sgrid_legend_filledcontours(self):
        params = copy(self.url_params)
        params.update(style='filledcontours_jet')
        self.do_test(params)

    def test_sgrid_legend_contours(self):
        params = copy(self.url_params)
        params.update(style='contours_jet')
        self.do_test(params)

    def test_sgrid_legend_contours_horizontal(self):
        params = copy(self.url_params)
        params.update(style='contours_jet', horizontal='true', width=500, height=100)
        self.do_test(params)
