'''
COPYRIGHT 2010 RPS ASA

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.
'''
import os
import pytz
import glob
from urlparse import urlparse
from datetime import datetime

from django.db import models
from django.conf import settings

from jsonfield import JSONField


class Dataset(models.Model):
    uri = models.CharField(max_length=1000)
    name = models.CharField(max_length=200, help_text="Name/ID to use. No special characters or spaces ('_','0123456789' and A-Z are allowed).")
    title = models.CharField(max_length=200, help_text="Human Readable Title")
    abstract = models.CharField(max_length=2000, help_text="Short Description of Dataset")
    keep_up_to_date = models.BooleanField(help_text="Check this box to keep the dataset up-to-date if changes are made to it on disk or remote server.", default=True)
    test_layer = models.CharField(max_length=200, help_text="Optional", blank=True)
    test_style = models.CharField(max_length=200, help_text="Optional", blank=True)
    display_all_timesteps = models.BooleanField(help_text="Check this box to display each time step in the GetCapabilities document, instead of just the range that the data spans.)", default=False)
    latitude_variable = models.CharField(blank=True, max_length=200, help_text="Name of latitude variable. Default: lat")
    longitude_variable = models.CharField(blank=True, max_length=200, help_text="Name of longitude variable. Default: lon")
    cache_last_updated = models.DateTimeField(null=True, editable=False)
    json = JSONField(blank=True, null=True, help_text="Arbitrary dataset-specific json blob")

    def __unicode__(self):
        return self.name

    def path(self):
        if urlparse(self.uri).scheme == "" and not self.uri.startswith("/"):
            # We have a relative path, make it absolute to the sciwms directory.
            return os.path.realpath(os.path.join(settings.PROJECT_ROOT, self.uri))
        else:
            return self.uri

    def update_cache(self, force=False):
        from sciwms.libs.data.caching import update_dataset_cache
        update_dataset_cache(self, force=force)
        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    def clear_cache(self):
        cache_file_list = glob.glob(os.path.join(settings.TOPOLOGY_PATH, self.safe_filename + '*'))
        for cache_file in cache_file_list:
            os.remove(cache_file)

    @property
    def safe_filename(self):
        return "".join(c for c in self.name if c.isalnum()).rstrip()

    @property
    def topology_file(self):
        return os.path.join(settings.TOPOLOGY_PATH, '{}.nc'.format(self.safe_filename))

    @property
    def domain_file(self):
        return os.path.join(settings.TOPOLOGY_PATH, '{}.domain'.format(self.safe_filename))

    @property
    def node_tree_root(self):
        return os.path.join(settings.TOPOLOGY_PATH, '{}.nodes').format(self.safe_filename)

    @property
    def cell_tree_root(self):
        return os.path.join(settings.TOPOLOGY_PATH, '{}.cells').format(self.safe_filename)

    @property
    def node_index_file(self):
        return '{}.idx'.format(self.node_tree_root)

    @property
    def node_data_file(self):
        return '{}.dat'.format(self.node_tree_root)

    @property
    def cell_index_file(self):
        return '{}.idx'.format(self.cell_tree_root)

    @property
    def cell_data_file(self):
        return '{}.dat'.format(self.cell_tree_root)



class VirtualLayer(models.Model):
    layer = models.CharField(max_length=200, help_text="Layer designation for the expression")
    layer_expression = models.CharField(max_length=200, help_text="Like u,v or Band1*Band2*Band3")
    datasets = models.ManyToManyField(Dataset, 
                                      help_text="Choose the datasets that this virtual layer applies to",
                                      blank=True,
                                      related_name='dataset_lyr_rel'
                                      )

    def __unicode__(self):
        return self.layer


class Group(models.Model):
    name = models.CharField(max_length=200)
    abstract = models.CharField(max_length=2000, blank=True, help_text="Short Description of the Group")
    datasets = models.ManyToManyField(Dataset, blank=True, help_text="Choose the datasets to add to this group, or create a dataset to add to this group")

    def __unicode__(self):
        return self.name


class Server(models.Model):
    # Server
    title = models.CharField(max_length=1000, help_text="Server Title", blank=True)
    abstract = models.CharField(max_length=2000, help_text="Server Abstract", blank=True)
    keywords = models.CharField(max_length=2000, help_text="Comma Separated List of Keywords", blank=True)

    # Contact
    contact_person = models.CharField(max_length=1000, help_text="Person to Contact (Optional)", blank=True)
    contact_organization = models.CharField(max_length=1000, help_text="Contact Organization (Optional)", blank=True)
    contact_position = models.CharField(max_length=1000, help_text="Contact Position (Optional)", blank=True)
    contact_street_address = models.CharField(max_length=1000, help_text="Street Address (Optional)", blank=True)
    contact_city_address = models.CharField(max_length=1000, help_text="Address: City (Optional)", blank=True)
    contact_state_address = models.CharField(max_length=1000, help_text="Address: State or Providence (Optional)", blank=True)
    contact_code_address = models.CharField(max_length=1000, help_text="Address: Postal Code (Optional)", blank=True)
    contact_country_address = models.CharField(max_length=1000, help_text="Address: Country (Optional)", blank=True)
    contact_telephone = models.CharField(max_length=1000, help_text="Contact Telephone Number (Optional)", blank=True)
    contact_email = models.CharField(max_length=1000, help_text="Contact Email Address (Optional)", blank=True)
