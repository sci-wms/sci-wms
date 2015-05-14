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
        add_dataset("legend_testing", "ugrid", "selfe_ugrid.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(name="legend_testing")
        d.clear_cache()
        d.delete()

    def setUp(self):
        self.dataset_name = 'legend_testing'
        self.url_params = dict(
            request = 'GetLegendGraphic',
            layer   = 'surface_salt',
        )

    def image_name(self):
        return '{}.png'.format(self.id().split('.')[-1])

    def do_test(self, params, write=True):
        response = self.client.get('/wms/datasets/{}'.format(self.dataset_name), params)
        self.assertEqual(response.status_code, 200)
        if write is True:
            with open(image_path(self.__class__.__name__, self.image_name()), "wb") as f:
                f.write(response.content)

    def test_pcolor(self):
        params = copy(self.url_params)
        params.update(styles='filledcontours_jet')
        self.do_test(params)

    def test_pcolor_no_label(self):
        params = copy(self.url_params)
        params.update(styles='filledcontours_jet', showlabel='false')
        self.do_test(params)

    def test_pcolor_custom_units(self):
        params = copy(self.url_params)
        params.update(styles='filledcontours_jet', unitlabel='somethingelse')
        self.do_test(params)

    def test_pcolor_colorscalerange(self):
        params = copy(self.url_params)
        params.update(styles='filledcontours_jet', colorscalerange='-1,1')
        self.do_test(params)
