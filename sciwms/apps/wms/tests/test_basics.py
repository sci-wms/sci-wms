import os
from django.test import TestCase, Client
from sciwms.apps.wms.tests import *

from sciwms.apps.wms.models import Dataset


class BasicTest(TestCase):
    def test_post_add(self):
        user = add_user()
        user.set_password('posting_dataset')
        user.save()

        uri = os.path.join(resource_path, "201220109.nc")
        params = {  "uri"       : uri,
                    "name"      : "test",
                    "title"     : "test",
                    "abstract"  : "my test dataset",
                    "update"    : "True",
                    "groups"    : ""
             }
        c = Client()
        c.login(username=user.username,
                password='posting_dataset')

        Dataset.objects.all().delete()  # Remove default datasets
        self.assertEqual(Dataset.objects.filter(uri=uri).count(), 0)
        request = c.post('/wms/add_dataset', params)
        self.assertEqual(request.status_code, 200)
        self.assertEqual(Dataset.objects.filter(uri=uri).count(), 1)
