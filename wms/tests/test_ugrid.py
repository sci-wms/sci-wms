# -*- coding: utf-8 -*-
from copy import copy

from django.test import TestCase
from wms.tests import add_server, add_group, add_user, add_dataset, image_path
from wms.models import Dataset, UGridDataset

from wms import logger

import pytest
xfail = pytest.mark.xfail


class TestUgrid(TestCase):

    @classmethod
    def setUpClass(cls):
        add_server()
        add_group()
        add_user()
        add_dataset("ugrid_testing", "ugrid", "selfe_ugrid.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(slug="ugrid_testing")
        d.delete()

    def setUp(self):
        self.dataset_slug = 'ugrid_testing'
        self.url_params = dict(
            service     = 'WMS',
            request     = 'GetMap',
            version     = '1.1.1',
            layers      = 'surface_salt',
            format      = 'image/png',
            transparent = 'true',
            height      = 256,
            width       = 256,
            srs         = 'EPSG:3857',
            bbox        = '-13756219.106426599,5811660.1345785195,-13736651.227185594,5831228.013819524'
        )

        self.gfi_params = dict(
            service      = 'WMS',
            request      = 'GetFeatureInfo',
            version      = '1.1.1',
            query_layers = 'surface_salt',
            info_format  = 'text/csv',
            srs          = 'EPSG:3857',
            bbox         = '-13756219.106426599,5811660.1345785195,-13736651.227185594,5831228.013819524',
            height       = 256,
            width        = 256,
            x            = 256,  # Top right
            y            = 0     # Top right
        )

        self.gmd_params = dict(
            service      = 'WMS',
            request      = 'GetMetadata',
            version      = '1.1.1',
            query_layers = 'surface_salt',
            srs          = 'EPSG:3857',
            bbox         = '-13756219.106426599,5811660.1345785195,-13736651.227185594,5831228.013819524',
            height       = 256,
            width        = 256
        )

    def image_name(self, fmt):
        return '{}.{}'.format(self.id().split('.')[-1], fmt)

    def test_identify(self):
        d = Dataset.objects.get(name=self.dataset_slug)
        klass = Dataset.identify(d.uri)
        assert klass == UGridDataset

    def do_test(self, params, fmt=None, write=True):
        fmt = fmt or 'png'
        response = self.client.get('/wms/datasets/{}'.format(self.dataset_slug), params)
        self.assertEqual(response.status_code, 200)
        outfile = image_path(self.__class__.__name__, self.image_name(fmt))
        if write is True:
            with open(outfile, "wb") as f:
                f.write(response.content)
        return outfile

    def test_filledcontours(self):
        params = copy(self.url_params)
        params.update(styles='filledcontours_jet')
        self.do_test(params)

    @xfail(reason="facets is not yet implemeted for UGRID datasets")
    def test_facets(self):
        params = copy(self.url_params)
        params.update(styles='facets_jet')
        self.do_test(params)

    @xfail(reason="pcolor is not yet implemeted for UGRID datasets")
    def test_pcolor(self):
        params = copy(self.url_params)
        params.update(styles='pcolor_jet')
        self.do_test(params)

    @xfail(reason="contours is not yet implemeted for UGRID datasets")
    def test_contours(self):
        params = copy(self.url_params)
        params.update(styles='contours_jet')
        self.do_test(params)

    def test_ugrid_gfi_single_variable_csv(self):
        params = copy(self.gfi_params)
        self.do_test(params, fmt='csv')

    def test_gfi_single_variable_csv_4326(self):
        params = copy(self.gfi_params)
        params['srs']  = 'EPSG:4326'
        params['bbox'] = '-123.57421875,46.19504211,-123.3984375,46.31658418'
        self.do_test(params, fmt='csv')

    def test_gfi_single_variable_tsv(self):
        params = copy(self.gfi_params)
        params['info_format']  = 'text/tsv'
        params['query_layers'] = 'surface_temp'
        self.do_test(params, fmt='tsv')

    def test_gfi_single_variable_json(self):
        params = copy(self.gfi_params)
        params['info_format']  = 'application/json'
        self.do_test(params, fmt='json')

    def test_ugrid_getmetadata_minmax(self):
        params = copy(self.gmd_params)
        params['item']  = 'minmax'
        self.do_test(params, fmt='json')

    def test_getCaps(self):
        params = dict(request='GetCapabilities')
        self.do_test(params, write=False)

    def test_create_layers(self):
        d = Dataset.objects.get(name=self.dataset_slug)
        assert d.layer_set.count() == 30

    def test_delete_cache_signal(self):
        d = add_dataset("ugrid_deleting", "ugrid", "selfe_ugrid.nc")
        self.assertTrue(d.has_cache())
        d.clear_cache()
        self.assertFalse(d.has_cache())
