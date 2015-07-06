# -*- coding: utf-8 -*-
from copy import copy

from datetime import datetime
import pandas as pd

from django.test import TestCase
from wms.tests import add_server, add_group, add_user, add_dataset, image_path
from wms.models import Dataset, SGridDataset

from wms import logger

import pytest
xfail = pytest.mark.xfail
#skip = pytest.skip


class TestSgrid(TestCase):

    @classmethod
    def setUpClass(cls):
        add_server()
        add_group()
        add_user()
        add_dataset("sgrid_testing", "sgrid", "coawst_sgrid.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(slug="sgrid_testing")
        d.delete()

    def setUp(self):
        self.dataset_slug = 'sgrid_testing'
        self.url_params = dict(
            service     = 'WMS',
            request     = 'GetMap',
            version     = '1.1.1',
            layers      = 'u',
            format      = 'image/png',
            transparent = 'true',
            height      = 256,
            width       = 256,
            srs         = 'EPSG:3857',
            bbox        = '-8140237.76425813,4852834.051769271,-7983694.730330088,5009377.085697313'
        )

        self.gfi_params = dict(
            service      = 'WMS',
            request      = 'GetFeatureInfo',
            version      = '1.1.1',
            query_layers = 'u',
            info_format  = 'text/csv',
            srs          = 'EPSG:3857',
            bbox         = '-8140237.76425813,4852834.051769271,-7983694.730330088,5009377.085697313',
            height       = 256,
            width        = 256,
            x            = 256,  # Top right
            y            = 0     # Top right
        )

    def image_name(self, fmt):
        return '{}.{}'.format(self.id().split('.')[-1], fmt)

    def test_identify(self):
        d = Dataset.objects.get(name=self.dataset_slug)
        klass = Dataset.identify(d.uri)
        assert klass == SGridDataset

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

    @xfail(reason="facets is not yet implemeted for SGRID datasets")
    def test_facets(self):
        params = copy(self.url_params)
        params.update(styles='facets_jet')
        self.do_test(params)

    def test_pcolor(self):
        params = copy(self.url_params)
        params.update(styles='pcolor_jet')
        self.do_test(params)

    @xfail(reason="contours is not yet implemeted for SGRID datasets")
    def test_contours(self):
        params = copy(self.url_params)
        params.update(styles='contours_jet')
        self.do_test(params)

    def test_vectors(self):
        params = copy(self.url_params)
        params.update(styles='vectors_jet', layers='u,v')
        self.do_test(params)

    def test_sgrid_gfi_single_variable_csv(self):
        params = copy(self.gfi_params)
        r = self.do_test(params, fmt='csv')
        df = pd.read_csv(r, index_col='time')
        logger.info(df)
        #assert df['time'][0] == datetime(2015, 04, 30, 0, 0, 0)
        assert df['x'][0] == -71.6979
        assert df['y'][0] == 40.9888
        assert df['u'][0] == -0.0315

    def test_sgrid_gfi_single_variable_csv_4326(self):
        params = copy(self.gfi_params)
        params['srs']  = 'EPSG:4326'
        params['bbox'] = '-73.125,39.90973623,-71.71875,40.97989807'
        r = self.do_test(params, fmt='csv')
        df = pd.read_csv(r, index_col='time')
        logger.info(df)
        #assert df['time'][0] == datetime(2015, 4, 30)
        assert df['x'][0] == -71.6979
        assert df['y'][0] == 40.9888
        assert df['u'][0] == -0.0315

    def test_gfi_single_variable_tsv(self):
        params = copy(self.gfi_params)
        params['info_format']  = 'text/tsv'
        self.do_test(params, fmt='tsv')

    def test_gfi_single_variable_json(self):
        params = copy(self.gfi_params)
        params['info_format']  = 'application/json'
        self.do_test(params, fmt='json')

    def test_getCaps(self):
        params = dict(request='GetCapabilities')
        self.do_test(params, write=False)

    def test_create_layers(self):
        d = Dataset.objects.get(name=self.dataset_slug)
        assert d.layer_set.count() == 15

    def test_delete_cache_signal(self):
        d = add_dataset("sgrid_deleting", "sgrid", "coawst_sgrid.nc")
        self.assertTrue(d.has_cache())
        d.clear_cache()
        self.assertFalse(d.has_cache())
