# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from sciwms.apps.wms.models import UGridDataset, SGridDataset, VirtualLayer
from sciwms.apps.wms.signals import ugrid_dataset_post_save, sgrid_dataset_post_save

from sciwms import logger


class TestDatasetList(APITestCase):

    def setUp(self):
        self.username = 'tester_tdl'
        self.user_email = 'tester_tdl@email.com'
        self.pwd = 'password'
        self.user = User.objects.create_user(username=self.username, email=self.user_email, password=self.pwd)
        self.dataset_1 = UGridDataset.objects.create(uri='fake_file_1.nc',
                                                     name='fake data 1',
                                                     title='some title 1',
                                                     abstract='some abstract 1',
                                                     keep_up_to_date=False)
        self.dataset_2 = SGridDataset.objects.create(uri='fake_file_2.nc',
                                                     name='fake data 2',
                                                     title='some title 2',
                                                     abstract='some abstract 2',
                                                     keep_up_to_date=False)
        self.ac = APIClient()
        self.ac.login(username=self.username, password=self.pwd)
        self.url = reverse('dataset-list')

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
                     'display_all_timesteps': False,
                     'type': 'ugrid'
                     }
        response = self.ac.post(self.url, test_data, format='json')
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_201_CREATED)

    def test_view_post_response_with_layers(self):
        url = reverse('dataset-list')
        test_data = {'uri': u'fake_file_4.nc',
                     'name': u'a fourth fake file',
                     'title': u'some title',
                     'abstract': u'a fourth fake abstract',
                     'keep_up_to_date': False,
                     'display_all_timesteps': False,
                     'type': 'sgrid'
                     }
        response = self.ac.post(url, test_data, format='json')
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_201_CREATED)


class TestDatasetDetail(APITestCase):

    def setUp(self):
        self.username = 'tester_tdd'
        self.user_email = 'tester_tdd@email.com'
        self.pwd = 'password'
        self.user = User.objects.create_user(username=self.username, email=self.user_email, password=self.pwd)
        self.dataset_1 = UGridDataset.objects.create(uri='fake_file_1.nc',
                                                     name='fake data 1',
                                                     title='some title 1',
                                                     abstract='some abstract 1',
                                                     keep_up_to_date=False)
        self.ac = APIClient()
        self.ac.login(username=self.username, password=self.pwd)
        self.url = reverse('dataset-detail', kwargs={'pk': self.dataset_1.pk})

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
                     'display_all_timesteps': False,
                     'type': 'ugrid'
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
