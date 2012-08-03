from django.db import models
from netCDF4 import Dataset

class Dataset(models.Model):
    uri = models.CharField(max_length=1000)
    name = models.CharField(max_length=200, help_text="No spaces please")
    keep_up_to_date = models.BooleanField()
    test_date = models.CharField(max_length=200, help_text="Optional (YYYY-MM-DDTHH:mm:ss)", blank=True)
    test_layer = models.CharField(max_length=200, help_text="Optional", blank=True)
    test_style = models.CharField(max_length=200, help_text="Optional", blank=True)

    


