'''
Created on Feb 27, 2015

@author: ayan
'''
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import signals
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from sciwms.apps.wms.models import Dataset, VirtualLayer
from sciwms.apps.wms.signals import dataset_post_save


class TestDatasetList(APITestCase):

    def setUp(self):
        self.username = 'tester_tdl'
        self.user_email = 'tester_tdl@email.com'
        self.pwd = 'password'
        self.user = User.objects.create_user(username=self.username, email=self.user_email, password=self.pwd)
        self.dataset_1 = Dataset(pk=1,
                                 uri='fake_file_1.nc',
                                 name='fake data 1',
                                 title='some title 1',
                                 abstract='some abstract 1',
                                 keep_up_to_date=False)
        self.dataset_2 = Dataset(pk=2,
                                 uri='fake_file_2.nc',
                                 name='fake data 2',
                                 title='some title 2',
                                 abstract='some abstract 2',
                                 keep_up_to_date=False)
        self.virtuallayer_1 = VirtualLayer(pk=1,
                                           layer='test_layer_1',
                                           layer_expression='test layer 1 expression')
        self.virtuallayer_2 = VirtualLayer(pk=2,
                                           layer='test_layer_2',
                                           layer_expression='test layer 2 expression')
        self.dataset_1.save()
        self.dataset_2.save()
        self.virtuallayer_1.save()
        self.virtuallayer_2.save()
        self.ac = APIClient()
        self.ac.login(username=self.username, password=self.pwd)
        self.url = reverse('dataset-list')
        # just want to test ability to post, so disable caching signal
        signals.post_save.disconnect(receiver=dataset_post_save, sender=Dataset)

    def test_view_get_response(self):
        response = self.ac.get(self.url)
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertContains(response, 'fake_file_2.nc')

    def test_view_post_response(self):
        test_data = {'uri': u'fake_file_3.nc',
                     'name': u'a third fake file',
                     'title': u'some title',
                     'abstract': u'a third fake abstract',
                     'keep_up_to_date': False,
                     'dataset_lyr_rel': [],
                     'display_all_timesteps': False,
                     }
        response = self.ac.post(self.url, test_data, format='json')
        status_code = response.status_code
        response_data = response.data
        del response_data['id']
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data, test_data)

    def test_view_post_response_with_layers(self):
        url = reverse('dataset-list')
        test_data = {'uri': u'fake_file_4.nc',
                     'name': u'a fourth fake file',
                     'title': u'some title',
                     'abstract': u'a fourth fake abstract',
                     'keep_up_to_date': False,
                     'dataset_lyr_rel': [1, 2],
                     'display_all_timesteps': False,
                     }
        response = self.ac.post(url, test_data, format='json')
        status_code = response.status_code
        response_data = response.data
        del response_data['id']
        layer_relationship = response_data['dataset_lyr_rel']
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        self.assertEqual(layer_relationship, [1, 2])


class TestDatasetDetail(APITestCase):

    def setUp(self):
        self.username = 'tester_tdd'
        self.user_email = 'tester_tdd@email.com'
        self.pwd = 'password'
        self.user = User.objects.create_user(username=self.username, email=self.user_email, password=self.pwd)
        self.dataset_1 = Dataset(pk=1,
                                 uri='fake_file_1.nc',
                                 name='fake data 1',
                                 title='some title 1',
                                 abstract='some abstract 1',
                                 keep_up_to_date=False)
        self.dataset_1.save()
        self.ac = APIClient()
        self.ac.login(username=self.username, password=self.pwd)
        self.url = reverse('dataset-detail', kwargs={'pk': 1})

    def test_get_dataset(self):
        response = self.ac.get(self.url)
        status_code = response.status_code
        resp_uri = response.data['uri']
        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(resp_uri, 'fake_file_1.nc')

    def test_put_dataset(self):
        new_filename = u'updated_file_1.nc'
        test_data = {'uri': new_filename,
                     'name': u'a third fake file',
                     'title': u'some title',
                     'abstract': u'a third fake abstract',
                     'keep_up_to_date': False,
                     'dataset_lyr_rel': [],
                     'display_all_timesteps': False,
                     }
        response = self.ac.put(self.url, test_data, format='json')
        status_code = response.status_code
        resp_uri = response.data['uri']
        self.assertEqual(resp_uri, new_filename)
        self.assertEqual(status_code, status.HTTP_200_OK)

    def test_delete_dataset(self):
        response = self.ac.delete(self.url)
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_204_NO_CONTENT)


class TestVirtualLayerList(APITestCase):

    def setUp(self):
        self.username = 'tester_vll'
        self.email = 'tester_vll@email.com'
        self.pwd = 'password'
        self.user = User.objects.create_user(username=self.username, email=self.email, password=self.pwd)
        self.virtuallayer_1 = VirtualLayer(pk=1,
                                           layer='fake layer 1',
                                           layer_expression='a, b, c')
        self.virtuallayer_2 = VirtualLayer(pk=2,
                                           layer='fake layer 2',
                                           layer_expression='x, y, z')
        self.dataset_1 = Dataset(pk=1,
                                 uri='fake_file_1.nc',
                                 name='fake data 1',
                                 title='some title 1',
                                 abstract='some abstract 1',
                                 keep_up_to_date=False)
        self.dataset_2 = Dataset(pk=2,
                                 uri='fake_file_2.nc',
                                 name='fake data 2',
                                 title='some title 2',
                                 abstract='some abstract 2',
                                 keep_up_to_date=False)
        self.virtuallayer_1.save()
        self.virtuallayer_2.save()
        self.dataset_1.save()
        self.dataset_2.save()
        self.ac = APIClient()
        self.ac.login(username=self.username, password=self.pwd)
        self.url = reverse('virtuallayers-list')

    def test_virtuallayer_get(self):
        response = self.ac.get(self.url)
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertContains(response, 'fake layer 1')

    def test_virtuallayer_post(self):
        test_data = {'layer': 'Ruthenium(III) chloride',
                     'layer_expression': 'RuCl3',
                     'datasets': []
                     }
        response = self.ac.post(self.url, test_data, format='json')
        status_code = response.status_code
        new_layer = response.data['layer']
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        self.assertEqual(new_layer, 'Ruthenium(III) chloride')

    def test_virtuallayer_post_with_ds_rel(self):
        test_data = {'layer': 'Sulfur hexafluoride',
                     'layer_expression': 'SF6',
                     'datasets': [1, 2]
                     }
        response = self.ac.post(self.url, test_data, format='json')
        status_code = response.status_code
        datasets = response.data['datasets']
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        self.assertEqual(datasets, [1, 2])


class TestVirtualLayerDetail(APITestCase):

    def setUp(self):
        self.username = 'tester_vld'
        self.email = 'tester_vld@email.com'
        self.pwd = 'password'
        self.user = User.objects.create_user(username=self.username, email=self.email, password=self.pwd)
        self.ac = APIClient()
        self.ac.login(username=self.username, password=self.pwd)
        self.virtuallayer_1 = VirtualLayer(pk=1,
                                           layer='Niobium(V) chloride',
                                           layer_expression='NbCl5')
        self.virtuallayer_1.save()
        self.url = reverse('virtuallayers-detail', kwargs={'pk': 1})

    def test_get_virtuallayer(self):
        response = self.ac.get(self.url)
        status_code = response.status_code
        layer = response.data['layer']
        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(layer, 'Niobium(V) chloride')

    def test_put_virtuallayer(self):
        test_data = {'layer': 'Niobium pentachloride',
                     'layer_expression': 'NbCl5',
                     'datasets': []
                     }
        response = self.ac.put(self.url, test_data, format='json')
        status_code = response.status_code
        layer = response.data['layer']
        layer_id = response.data['id']
        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(layer, 'Niobium pentachloride')
        self.assertEqual(layer_id, 1)

    def test_delete_virtuallayer(self):
        response = self.ac.delete(self.url)
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_204_NO_CONTENT)
