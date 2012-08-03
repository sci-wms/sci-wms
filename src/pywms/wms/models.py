from django.db import models
from netCDF4 import Dataset

class Dataset(models.Model):
    uri = models.CharField(max_length=1000)
    name = models.CharField(max_length=200)
    keep_up_to_date = models.BooleanField()
    test_date = models.CharField(max_length=200)
    test_layer = models.CharField(max_length=200)
    test_style = models.CharField(max_length=200)

    


