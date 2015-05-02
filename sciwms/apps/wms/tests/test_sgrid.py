from django.test import TestCase
from sciwms.apps.wms.tests import add_server, add_group, add_user, add_dataset
from sciwms.apps.wms.models import Dataset


class TestCgrid(TestCase):

    @classmethod
    def setUpClass(cls):
        add_server()
        add_group()
        add_user()
        add_dataset("sgrid_testing", "sgrid", "coawst_sgrid.nc")

    @classmethod
    def tearDownClass(cls):
        d = Dataset.objects.get(name="sgrid_testing")
        d.clear_cache()
        d.delete()

    def test_pcolor(self):
        response = self.client.get('/wms/datasets/sgrid_testing/?LAYERS=u%2Cv&TRANSPARENT=TRUE&STYLES=pcolor_average_jet_None_None_cell_False&TIME=&ELEVATION=0&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image%2Fpng&SRS=EPSG%3A3857&BBOX=-8543030.3273202,5492519.0747705,-8401010.3287862,5542356.0172055&WIDTH=929&HEIGHT=326')
        self.assertEqual(response.status_code, 200)

    def test_contours(self):
        response = self.client.get('/wms/datasets/sgrid_testing/?LAYERS=u%2Cv&TRANSPARENT=TRUE&STYLES=contours_average_jet_None_None_cell_False&TIME=&ELEVATION=0&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image%2Fpng&SRS=EPSG%3A3857&BBOX=-8543030.3273202,5492519.0747705,-8401010.3287862,5542356.0172055&WIDTH=929&HEIGHT=326')
        self.assertEqual(response.status_code, 200)

    def test_filledcontours(self):
        response = self.client.get('/wms/datasets/sgrid_testing/?LAYERS=u%2Cv&TRANSPARENT=TRUE&STYLES=filledcontours_average_jet_None_None_cell_False&TIME=&ELEVATION=0&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image%2Fpng&SRS=EPSG%3A3857&BBOX=-8543030.3273202,5492519.0747705,-8401010.3287862,5542356.0172055&WIDTH=929&HEIGHT=326')
        self.assertEqual(response.status_code, 200)

    def test_vectors(self):
        response = self.client.get('/wms/datasets/sgrid_testing/?LAYERS=u%2Cv&TRANSPARENT=TRUE&STYLES=vectors_average_jet_None_None_cell_False&TIME=&ELEVATION=0&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image%2Fpng&SRS=EPSG%3A3857&BBOX=-8543030.3273202,5492519.0747705,-8401010.3287862,5542356.0172055&WIDTH=929&HEIGHT=326')
        self.assertEqual(response.status_code, 200)

    def test_getCaps(self):
        response = self.client.get('/wms/datasets/sgrid_testing/?REQUEST=GetCapabilities')
        self.assertEqual(response.status_code, 200)

    def test_create_layers(self):
        # Layers created in creation signal
        d = Dataset.objects.get(name='sgrid_testing')
        assert d.layer_set.count() == 12
