# -*- coding: utf-8 -*-
from django.test import TestCase
from wms.tests import add_server, add_group, add_user, add_dataset
from wms.models import Dataset, VirtualLayer, Variable

from wms import logger


class TestLayerDefaults(TestCase):

    @classmethod
    def setUpClass(cls):
        add_server()
        add_group()
        add_user()
        add_dataset("sgrid_default_testing", "sgrid", "coawst_sgrid.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(slug="sgrid_default_testing")
        d.delete()

    def setUp(self):
        self.dataset_slug = 'sgrid_default_testing'

    def test_create_layers(self):
        vl = Dataset.objects.get(slug=self.dataset_slug).virtuallayer_set.get(var_name='u,v')

        defs = vl.defaults
        assert defs.min is None
        assert defs.max is None
        assert defs.logscale is None

        Variable.objects.create(std_name=vl.std_name,
                                units=vl.units,
                                default_min=1.,
                                default_max=10.,
                                logscale=True)

        defs = vl.defaults
        assert defs.min == 1.
        assert defs.max == 10.
        assert defs.logscale is True

        # Now turn off the logscale at the Layer level
        vl.logscale = False
        vl.save()
        defs = vl.defaults
        assert defs.min == 1.
        assert defs.max == 10.
        assert defs.logscale is False

        vl.default_max = 900.
        vl.save()
        defs = vl.defaults
        assert defs.min == 1.
        assert defs.max == 900.
        assert defs.logscale is False
