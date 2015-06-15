from copy import copy
import unittest

from django.test import TestCase
from wms.tests import add_server, add_group, add_user, add_dataset, image_path
from wms.models import Dataset, SGridDataset


class TestSgrid(TestCase):

    @classmethod
    def setUpClass(cls):
        add_server()
        add_group()
        add_user()
        add_dataset("sgrid_testing", "sgrid", "coawst_sgrid.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(name="sgrid_testing")
        d.delete()

    def setUp(self):
        self.dataset_name = 'sgrid_testing'
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

    def image_name(self):
        return '{}.png'.format(self.id().split('.')[-1])

    def test_identify(self):
        d = Dataset.objects.get(name=self.dataset_name)
        klass = Dataset.identify(d.uri)
        assert klass == SGridDataset

    def do_test(self, params, write=True):
        response = self.client.get('/wms/datasets/{}'.format(self.dataset_name), params)
        self.assertEqual(response.status_code, 200)
        if write is True:
            with open(image_path(self.__class__.__name__, self.image_name()), "wb") as f:
                f.write(response.content)

    @unittest.skip("filledcontours is not yet implemeted for SGRID datasets")
    def test_filledcontours(self):
        params = copy(self.url_params)
        params.update(styles='filledcontours_jet')
        self.do_test(params)

    @unittest.skip("facets is not yet implemeted for SGRID datasets")
    def test_facets(self):
        params = copy(self.url_params)
        params.update(styles='facets_jet')
        self.do_test(params)

    def test_pcolor(self):
        params = copy(self.url_params)
        params.update(styles='pcolor_jet')
        self.do_test(params)

    @unittest.skip("contours is not yet implemeted for SGRID datasets")
    def test_contours(self):
        params = copy(self.url_params)
        params.update(styles='contours_jet')
        self.do_test(params)

    def test_vectors(self):
        params = copy(self.url_params)
        params.update(styles='vectors_jet', layers='u,v')
        self.do_test(params)

    def test_getCaps(self):
        params = dict(request='GetCapabilities')
        self.do_test(params, write=False)

    def test_create_layers(self):
        d = Dataset.objects.get(name=self.dataset_name)
        assert d.layer_set.count() == 15

    def test_delete_cache_signal(self):
        d = add_dataset("sgrid_deleting", "sgrid", "coawst_sgrid.nc")
        self.assertTrue(d.has_cache())
        d.clear_cache()
        self.assertFalse(d.has_cache())
