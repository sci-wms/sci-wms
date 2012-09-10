from django.db import models
from netCDF4 import Dataset

class Dataset(models.Model):
    uri             = models.CharField(max_length=1000)
    name            = models.CharField(max_length=200, help_text="Name/ID to use. No special characters or spaces ('-','_','0123456789' are allowed).")
    title           = models.CharField(max_length=200, help_text="Human Readable Title")
    abstract        = moeels.CharField(max_length=200, help_text="Short Description of Dataset")
    keep_up_to_date = models.BooleanField()
    test_date       = models.CharField(max_length=200, help_text="Optional (YYYY-MM-DDTHH:mm:ss)", blank=True)
    test_layer      = models.CharField(max_length=200, help_text="Optional", blank=True)
    test_style      = models.CharField(max_length=200, help_text="Optional", blank=True)
    test_style      = models.CharField(max_length=200, help_text="Optional", blank=True)
    
class Server(models.Model):
    # Server
    title    = models.CharField(max_length=1000, help_text="Server Title", blank=True)
    abstract = models.CharField(max_length=2000, help_text="Server Abstract", blank=True)
    keywords = models.CharField(max_length=2000, help_text="Comma Separated List of Keywords", blank=True)
    
    # Contact
    contact_person          = models.CharField(max_length=1000, help_text="Person to Contact (Optional)", blank=True)
    contact_organization    = models.CharField(max_length=1000, help_text="Contact Organization (Optional)", blank=True)
    contact_position        = models.CharField(max_length=1000, help_text="Contact Position (Optional)", blank=True)
    contact_street_address  = models.CharField(max_length=1000, help_text="Street Address (Optional)", blank=True)
    contact_city_address    = models.CharField(max_length=1000, help_text="Address: City (Optional)", blank=True)
    contact_state_address   = models.CharField(max_length=1000, help_text="Address: State or Providence (Optional)", blank=True)
    contact_code_address    = models.CharField(max_length=1000, help_text="Address: Postal Code (Optional)", blank=True)
    contact_country_address = models.CharField(max_length=1000, help_text="Address: Country (Optional)", blank=True)
    contact_telephone       = models.CharField(max_length=1000, help_text="Contact Telephone Number (Optional)", blank=True)
    contact_email           = models.CharField(max_length=1000, help_text="Contact Email Address (Optional)", blank=True)

    


