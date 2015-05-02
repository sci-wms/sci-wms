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

import matplotlib.pyplot as plt

from typedmodels import TypedModel
from pyugrid import UGrid
#from pysgrid import SGrid
from pyaxiom.netcdf import EnhancedDataset, EnhancedMFDataset
from sciwms.libs.data.custom_exceptions import NonCompliantDataset

from sciwms.libs.data.utils import get_nc_variable_values
from sciwms import logger


class Dataset(TypedModel):
    uri = models.CharField(max_length=1000)
    name = models.CharField(max_length=200, unique=True, help_text="Name/ID to use. No special characters or spaces ('_','0123456789' and A-Z are allowed).")
    title = models.CharField(max_length=200, help_text="Human Readable Title")
    abstract = models.CharField(max_length=2000, help_text="Short Description of Dataset")
    keep_up_to_date = models.BooleanField(help_text="Check this box to keep the dataset up-to-date if changes are made to it on disk or remote server.", default=True)
    display_all_timesteps = models.BooleanField(help_text="Check this box to display each time step in the GetCapabilities document, instead of just the range that the data spans.)", default=False)
    cache_last_updated = models.DateTimeField(null=True, editable=False)
    json = JSONField(blank=True, null=True, help_text="Arbitrary dataset-specific json blob")

    def __unicode__(self):
        return self.name

    def path(self):
        if urlparse(self.uri).scheme == "" and not self.uri.startswith("/"):
            # We have a relative path, make it absolute to the sciwms directory.
            return str(os.path.realpath(os.path.join(settings.PROJECT_ROOT, self.uri)))
        else:
            return str(self.uri)

    def netcdf4_dataset(self):
        try:
            return EnhancedDataset(self.path())
        except:
            try:
                return EnhancedMFDataset(self.path(), aggdim='time')
            except:
                return None

    def update_cache(self, force=False):
        raise NotImplementedError("Implement in subclasses")

    def clear_cache(self):
        cache_file_list = glob.glob(os.path.join(settings.TOPOLOGY_PATH, self.safe_filename + '*'))
        for cache_file in cache_file_list:
            os.remove(cache_file)

    def analyze_virtual_layers(self):
        nc = self.netcdf4_dataset()
        if nc is not None:
            # Earth Projected Sea Water Velocity
            u_names = ['eastward_sea_water_velocity', 'eastward_sea_water_velocity_assuming_no_tide']
            v_names = ['northward_sea_water_velocity', 'northward_sea_water_velocity_assuming_no_tide']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            VirtualLayer.make_vector_layer(us, vs, 'sea_water_velocity', 'vectors', self.id)

            # Grid projected Sea Water Velocity
            u_names = ['x_sea_water_velocity', 'grid_eastward_sea_water_velocity']
            v_names = ['y_sea_water_velocity', 'grid_northward_sea_water_velocity']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            VirtualLayer.make_vector_layer(us, vs, 'grid_sea_water_velocity', 'vectors', self.id)

            # Earth projected Winds
            u_names = ['eastward_wind']
            v_names = ['northward_wind']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            VirtualLayer.make_vector_layer(us, vs, 'winds', 'barbs', self.id)

            # Grid projected Winds
            u_names = ['x_wind', 'grid_eastward_wind']
            v_names = ['northward_wind', 'grid_northward_wind']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            VirtualLayer.make_vector_layer(us, vs, 'grid_winds', 'barbs', self.id)

            # Earth projected Ice velocity
            u_names = ['eastward_sea_ice_velocity']
            v_names = ['northward_sea_ice_velocity']
            us = nc.get_variables_by_attributes(standard_name=lambda v: v in u_names)
            vs = nc.get_variables_by_attributes(standard_name=lambda v: v in v_names)
            VirtualLayer.make_vector_layer(us, vs, 'sea_ice_velocity', 'vectors', self.id)

            nc.close()

    def process_layers(self):
        nc = self.netcdf4_dataset()
        if nc is not None:

            for v in nc.variables:
                l, _ = Layer.objects.get_or_create(dataset_id=self.id, var_name=v)

                nc_var = nc.variables[v]
                if hasattr(nc_var, 'valid_range'):
                    l.default_min = nc_var.valid_range[0]
                    l.default_max = nc_var.valid_range[-1]
                # valid_min and valid_max take presendence
                if hasattr(nc_var, 'valid_min'):
                    l.default_min = nc_var.valid_min
                if hasattr(nc_var, 'valid_max'):
                    l.default_max = nc_var.valid_max

                if hasattr(nc_var, 'standard_name'):
                    std_name = nc_var.standard_name
                    l.std_name = std_name

                    if len(nc_var.dimensions) > 1:
                        l.active = True

                # Set some standard styles
                l.styles = Style.defaults()
                l.save()

            nc.close()

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


class UGridDataset(Dataset):
    def update_cache(self, force=False):
        try:
            nc = self.netcdf4_dataset()
            ug = UGrid.from_nc_dataset(nc=nc)
            ug.save_as_netcdf(self.topology_file)

            if not os.path.exists(self.topology_file):
                logger.error("Failed to create topology_file cache for Dataset '{}'".format(self.dataset))
                return

            cached_nc = EnhancedDataset(self.topology_file, mode='a')

            # add time to the cached topology
            time_var = nc.get_variables_by_attributes(standard_name='time')[0]
            time_vals = time_var[:]
            if time_vals is not None:
                cached_nc.createDimension('time', size=time_vals.size)
                if time_vals.ndim > 1:  # deal with one dimensional time for now
                    pass
                else:
                    cached_time_var = cached_nc.createVariable(varname='time',
                                                               datatype='f8',
                                                               dimensions=('time',))
                    cached_time_var[:] = time_vals[:]
                    cached_time_var.units = time_var.units
            cached_nc.close()
        except:
            raise
        finally:
            if nc is not None:
                nc.close()

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()


class SGridDataset(Dataset):
    def update_cache(self, force=False):
        return  # Remove this line after SGRID library is functional
        try:
            nc = self.netcdf4_dataset()
            #sg = SGrid.from_nc_dataset(nc=nc)  # Uncomment after SGRID library is functional
            #sg.save_as_netcdf(self.topology_file)  # Uncomment after SGRID library is functional

            if not os.path.exists(self.topology_file):
                logger.error("Failed to create topology_file cache for Dataset '{}'".format(self.dataset))
                return

            cached_nc = EnhancedDataset(self.topology_file, mode='a')

            # add time to the cached topology
            time_var = nc.get_variables_by_attributes(standard_name='time')[0]
            time_vals = time_var[:]
            if time_vals is not None:
                cached_nc.createDimension('time', size=time_vals.size)
                if time_vals.ndim > 1:  # deal with one dimensional time for now
                    pass
                else:
                    cached_time_var = cached_nc.createVariable(varname='time',
                                                               datatype='f8',
                                                               dimensions=('time',))
                    cached_time_var[:] = time_vals[:]
                    cached_time_var.units = time_var.units
            cached_nc.close()
        except:
            raise
        finally:
            if nc is not None:
                nc.close()

        self.cache_last_updated = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()


class LayerBase(models.Model):
    var_name    = models.CharField(max_length=200, help_text="Variable name from dataset")
    std_name    = models.CharField(max_length=200, blank=True, help_text="The 'standard_name' from the dataset variable")
    description = models.CharField(max_length=200, blank=True, help_text="Descriptive name of this layer, optional")
    dataset     = models.ForeignKey('Dataset')
    active      = models.BooleanField(default=False)
    styles      = models.ManyToManyField('Style')
    default_min = models.FloatField(null=True, default=None, blank=True, help_text="If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.")
    default_max = models.FloatField(null=True, default=None, blank=True, help_text="If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.")

    class Meta:
        abstract = True
        ordering = ('var_name',)

    def __unicode__(self):
        z = self.var_name
        z += ' ({})'.format(self.std_name) if self.std_name else ''
        z += ' - Active: {}'.format(self.active)
        return z


class Layer(LayerBase):
    pass


class VirtualLayer(LayerBase):

    @classmethod
    def make_vector_layer(cls, us, vs, std_name, style, dataset_id):
        for u in us:
            for v in vs:
                if u.standard_name.split('_')[1:] == v.standard_name.split('_')[1:]:
                    try:
                        vl = VirtualLayer.objects.create(var_name='{},{}'.format(u._name, v._name),
                                                         std_name=std_name,
                                                         description="U ({}) and V ({}) vectors".format(u._name, v._name),
                                                         dataset_id=dataset_id,
                                                         active=True)
                        vl.styles.add(Style.objects.get(colormap='jet', image_type=style))
                        vl.save()
                        break
                    except:
                        raise


class Style(models.Model):
    description = models.CharField(max_length=200, blank=True, help_text="Descriptive name of this style, optional")
    colormap    = models.CharField(max_length=200,
                                   help_text="The matplotlib colormaps. See: http://matplotlib.org/1.2.1/examples/pylab_examples/show_colormaps.html.",
                                   choices=sorted((m, m) for m in plt.cm.datad if not m.endswith("_r")))
    image_type  = models.CharField(max_length=200, default="filledcontours", choices=(("filledcontours", "filledcontours"),
                                                                                      ("contours", "contours"),
                                                                                      ("pcolor", "pcolor"),
                                                                                      ("facets", "facets"),
                                                                                      ("composite", "composite"),
                                                                                      ("vectors", "vectors"),
                                                                                      ("barbs", "barbs")))

    @classmethod
    def defaults(cls):
        return Style.objects.filter(colormap='jet', image_type__in=['filledcontours', 'contours', 'facets', 'pcolor'])

    @property
    def code(self):
        return '{}_{}'.format(self.image_type, self.colormap)

    def __unicode__(self):
        return '{}_{}'.format(self.image_type, self.colormap)


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
