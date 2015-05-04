# -*- coding: utf-8 -*-
import os
import glob
from urlparse import urlparse


from django.db import models
from typedmodels import TypedModel
from jsonfield import JSONField

from pyaxiom.netcdf import EnhancedDataset, EnhancedMFDataset

from wms.models import VirtualLayer, Layer, Style
from django.conf import settings


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
