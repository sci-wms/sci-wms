# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime

from django.test import TestCase
from wms.tests import add_server, add_group, add_user, add_dataset, image_path
from wms.models import Dataset, UGridTideDataset

from wms import logger

import pytest
xfail = pytest.mark.xfail


class TestUgridTides(TestCase):

    @classmethod
    def setUpClass(cls):
        add_server()
        add_group()
        add_user()
        add_dataset("ugrid_tides_testing", "ugrid_tides", "shinnecock.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(slug="ugrid_tides_testing")
        d.delete()

    def setUp(self):
        self.dataset_slug = 'ugrid_tides_testing'
        self.url_params = dict(
            service     = 'WMS',
            request     = 'GetMap',
            version     = '1.1.1',
            layers      = 'u,v',
            format      = 'image/png',
            transparent = 'true',
            height      = 256,
            width       = 256,
            srs         = 'EPSG:3857',
            bbox        = '-8071750.186914611,4980025.266835802,-8061966.247294108,4989809.2064563045',
        )

        self.gfi_params = dict(
            service      = 'WMS',
            request      = 'GetFeatureInfo',
            version      = '1.1.1',
            query_layers = 'u,v',
            info_format  = 'text/csv',
            srs          = 'EPSG:3857',
            bbox         = '-8071750.186914611,4980025.266835802,-8061966.247294108,4989809.2064563045',
            height       = 256,
            width        = 256,
            x            = 256,  # Top right
            y            = 0     # Top right
        )

        self.gmd_params = dict(
            service      = 'WMS',
            request      = 'GetMetadata',
            version      = '1.1.1',
            query_layers = 'u,v',
            srs          = 'EPSG:3857',
            bbox         = '-8071750.186914611,4980025.266835802,-8061966.247294108,4989809.2064563045',
            height       = 256,
            width        = 256
        )

    def image_name(self, fmt):
        return '{}.{}'.format(self.id().split('.')[-1], fmt)

    def test_identify(self):
        d = Dataset.objects.get(name=self.dataset_slug)
        klass = Dataset.identify(d.uri)
        assert klass == UGridTideDataset

    def do_test(self, params, fmt=None, write=True):
        fmt = fmt or 'png'
        response = self.client.get('/wms/datasets/{}'.format(self.dataset_slug), params)
        self.assertEqual(response.status_code, 200)
        outfile = image_path(self.__class__.__name__, self.image_name(fmt))
        if write is True:
            with open(outfile, "wb") as f:
                f.write(response.content)
        return outfile

    def test_ugrid_tides_vectorscale(self):
        params = copy(self.url_params)
        params['vectorscale'] = 10
        params['styles'] = 'vectors_cubehelix'
        self.do_test(params)

    def test_ugrid_tides_vectorstep(self):
        params = copy(self.url_params)
        params['vectorstep'] = 10
        params['styles'] = 'vectors_cubehelix'
        self.do_test(params)

    def test_ugrid_tides_default_styles(self):
        params = copy(self.url_params)
        self.do_test(params)

    @xfail(reason="filledcontours is not yet implemeted for UTIDE datasets")
    def test_ugrid_tides_filledcontours(self):
        params = copy(self.url_params)
        params.update(styles='filledcontours_cubehelix')
        self.do_test(params)

    @xfail(reason="filledcontours is not yet implemeted for UTIDE datasets")
    def test_ugrid_tides_filledcontours_50(self):
        params = copy(self.url_params)
        params.update(styles='filledcontours_cubehelix', numcontours=50)
        self.do_test(params)

    @xfail(reason="pcolor is not yet implemeted for UTIDE datasets")
    def test_ugrid_tides_pcolor(self):
        params = copy(self.url_params)
        params.update(styles='pcolor_cubehelix')
        self.do_test(params)

    @xfail(reason="pcolor is not yet implemeted for UTIDE datasets")
    def test_ugrid_tides_pcolor_logscale(self):
        params = copy(self.url_params)
        params.update(styles='pcolor_cubehelix', logscale=True)
        self.do_test(params)

    @xfail(reason="facets is not yet implemeted for UTIDE datasets")
    def test_ugrid_tides_facets(self):
        params = copy(self.url_params)
        params.update(styles='facets_cubehelix')
        self.do_test(params)

    @xfail(reason="contours is not yet implemeted for UTIDE datasets")
    def test_ugrid_tides_contours(self):
        params = copy(self.url_params)
        params.update(styles='contours_cubehelix')
        self.do_test(params)

    @xfail(reason="contours is not yet implemeted for UTIDE datasets")
    def test_ugrid_tides_contours_50(self):
        params = copy(self.url_params)
        params.update(styles='contours_cubehelix', numcontours=50)
        self.do_test(params)

    @xfail(reason="GetFeatureInfo is not yet implemeted for UTIDE datasets")
    def test_ugrid_tides_gfi_single_variable_csv(self):
        params = copy(self.gfi_params)
        self.do_test(params, fmt='csv')

    def test_ugrid_tides_getmetadata_minmax(self):
        params = copy(self.gmd_params)
        params['item']  = 'minmax'
        self.do_test(params, fmt='json')

    def test_ugrid_tides_getCaps(self):
        params = dict(request='GetCapabilities')
        self.do_test(params, fmt='xml', write=True)

    def test_ugrid_tides_create_layers(self):
        d = Dataset.objects.get(name=self.dataset_slug)
        assert d.layer_set.count() == 0
        assert d.virtuallayer_set.count() == 1
        assert d.virtuallayer_set.first().var_name == 'u,v'
        assert d.virtuallayer_set.first().access_name == 'u'
