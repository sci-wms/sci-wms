from django.test import TestCase
from wms.tests import *
from wms.models import Dataset

from sciwms import logger


class TestGetLegendGraphic(TestCase):

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

    def test_pcolor(self):
        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=facets_average_jet_-1_1_cell_False&layer=u%2Cv')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=facets_average_jet_-1_1_cell_False&layer=u%2Cv&showlabel=false')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=facets_average_jet_-1_1_cell_False&layer=u%2Cv&units=somethingelse')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=facets_average_jet_None_None_cell_False&layer=u%2Cv&colorscalerange=-1,1')
        self.assertEqual(response.status_code, 200)

    def test_contours(self):
        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=contours_average_jet_-1_1_cell_False&layer=u%2Cv')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=contours_average_jet_-1_1_cell_False&layer=u%2Cv&showlabel=false')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=contours_average_jet_-1_1_cell_False&layer=u%2Cv&units=somethingelse')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=contours_average_jet_None_None_cell_False&layer=u%2Cv&colorscalerange=-1,1')
        self.assertEqual(response.status_code, 200)

    def test_filledcontours(self):
        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=filledcontours_average_jet_-1_1_cell_False&layer=u%2Cv')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=filledcontours_average_jet_-1_1_cell_False&layer=u%2Cv&showlabel=false')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=filledcontours_average_jet_-1_1_cell_False&layer=u%2Cv&units=somethingelse')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=filledcontours_average_jet_None_None_cell_False&layer=u%2Cv&colorscalerange=-1,1')
        self.assertEqual(response.status_code, 200)

    def test_vectors(self):
        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=vectors_average_jet_-1_1_cell_False&layer=u%2Cv')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=vectors_average_jet_-1_1_cell_False&layer=u%2Cv&showlabel=false')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=vectors_average_jet_-1_1_cell_False&layer=u%2Cv&units=somethingelse')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/wms/datasets/legend_testing/?request=GetLegendGraphic&styles=vectors_average_jet_None_None_cell_False&layer=u%2Cv&colorscalerange=-1,1')
        self.assertEqual(response.status_code, 200)
