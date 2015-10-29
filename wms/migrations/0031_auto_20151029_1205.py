# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import autoslug.fields
import wms.models.datasets.base


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0030_auto_20150716_1648'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DatasetOriginal',
        ),
        migrations.AlterField(
            model_name='dataset',
            name='abstract',
            field=models.CharField(help_text='Short Description of Dataset', max_length=2000),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='display_all_timesteps',
            field=models.BooleanField(help_text='Check this box to display each time step in the GetCapabilities document, instead of just the range that the data spans.)', default=False),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='json',
            field=jsonfield.fields.JSONField(help_text='Arbitrary dataset-specific json blob', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='keep_up_to_date',
            field=models.BooleanField(help_text='Check this box to keep the dataset up-to-date if changes are made to it on disk or remote server.', default=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='name',
            field=models.CharField(help_text="Name/ID to use. No special characters or spaces ('_','0123456789' and A-Z are allowed).", max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from='name', editable=False, slugify=wms.models.datasets.base.only_underscores),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='title',
            field=models.CharField(help_text='Human Readable Title', max_length=200),
        ),
        migrations.AlterField(
            model_name='group',
            name='abstract',
            field=models.CharField(help_text='Short Description of the Group', blank=True, max_length=2000),
        ),
        migrations.AlterField(
            model_name='group',
            name='datasets',
            field=models.ManyToManyField(help_text='Choose the datasets to add to this group, or create a dataset to add to this group', blank=True, to='wms.Dataset'),
        ),
        migrations.AlterField(
            model_name='layer',
            name='default_max',
            field=models.FloatField(help_text='If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.', blank=True, null=True, default=None),
        ),
        migrations.AlterField(
            model_name='layer',
            name='default_min',
            field=models.FloatField(help_text='If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.', blank=True, null=True, default=None),
        ),
        migrations.AlterField(
            model_name='layer',
            name='description',
            field=models.CharField(help_text='Descriptive name of this layer, optional', blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='layer',
            name='logscale',
            field=models.NullBooleanField(help_text='If this dataset variable should default to a log scale', default=None),
        ),
        migrations.AlterField(
            model_name='layer',
            name='std_name',
            field=models.CharField(help_text="The 'standard_name' from the dataset variable", blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='layer',
            name='units',
            field=models.CharField(help_text="The 'units' from the dataset variable", blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='layer',
            name='var_name',
            field=models.CharField(help_text='Variable name from dataset', max_length=200),
        ),
        migrations.AlterField(
            model_name='server',
            name='abstract',
            field=models.CharField(help_text='Server Abstract', blank=True, max_length=2000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_city_address',
            field=models.CharField(help_text='Address: City (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_code_address',
            field=models.CharField(help_text='Address: Postal Code (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_country_address',
            field=models.CharField(help_text='Address: Country (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_email',
            field=models.CharField(help_text='Contact Email Address (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_organization',
            field=models.CharField(help_text='Contact Organization (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_person',
            field=models.CharField(help_text='Person to Contact (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_position',
            field=models.CharField(help_text='Contact Position (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_state_address',
            field=models.CharField(help_text='Address: State or Providence (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_street_address',
            field=models.CharField(help_text='Street Address (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='contact_telephone',
            field=models.CharField(help_text='Contact Telephone Number (Optional)', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='server',
            name='keywords',
            field=models.CharField(help_text='Comma Separated List of Keywords', blank=True, max_length=2000),
        ),
        migrations.AlterField(
            model_name='server',
            name='title',
            field=models.CharField(help_text='Server Title', blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='style',
            name='colormap',
            field=models.CharField(help_text='The matplotlib colormaps. See: http://matplotlib.org/1.2.1/examples/pylab_examples/show_colormaps.html.', choices=[('Accent', 'Accent'), ('Blues', 'Blues'), ('BrBG', 'BrBG'), ('BuGn', 'BuGn'), ('BuPu', 'BuPu'), ('CMRmap', 'CMRmap'), ('Dark2', 'Dark2'), ('GnBu', 'GnBu'), ('Greens', 'Greens'), ('Greys', 'Greys'), ('OrRd', 'OrRd'), ('Oranges', 'Oranges'), ('PRGn', 'PRGn'), ('Paired', 'Paired'), ('Pastel1', 'Pastel1'), ('Pastel2', 'Pastel2'), ('PiYG', 'PiYG'), ('PuBu', 'PuBu'), ('PuBuGn', 'PuBuGn'), ('PuOr', 'PuOr'), ('PuRd', 'PuRd'), ('Purples', 'Purples'), ('RdBu', 'RdBu'), ('RdGy', 'RdGy'), ('RdPu', 'RdPu'), ('RdYlBu', 'RdYlBu'), ('RdYlGn', 'RdYlGn'), ('Reds', 'Reds'), ('Set1', 'Set1'), ('Set2', 'Set2'), ('Set3', 'Set3'), ('Spectral', 'Spectral'), ('Wistia', 'Wistia'), ('YlGn', 'YlGn'), ('YlGnBu', 'YlGnBu'), ('YlOrBr', 'YlOrBr'), ('YlOrRd', 'YlOrRd'), ('afmhot', 'afmhot'), ('autumn', 'autumn'), ('binary', 'binary'), ('bone', 'bone'), ('brg', 'brg'), ('bwr', 'bwr'), ('cool', 'cool'), ('coolwarm', 'coolwarm'), ('copper', 'copper'), ('cubehelix', 'cubehelix'), ('flag', 'flag'), ('gist_earth', 'gist_earth'), ('gist_gray', 'gist_gray'), ('gist_heat', 'gist_heat'), ('gist_ncar', 'gist_ncar'), ('gist_rainbow', 'gist_rainbow'), ('gist_stern', 'gist_stern'), ('gist_yarg', 'gist_yarg'), ('gnuplot', 'gnuplot'), ('gnuplot2', 'gnuplot2'), ('gray', 'gray'), ('hot', 'hot'), ('hsv', 'hsv'), ('jet', 'jet'), ('nipy_spectral', 'nipy_spectral'), ('ocean', 'ocean'), ('pink', 'pink'), ('prism', 'prism'), ('rainbow', 'rainbow'), ('seismic', 'seismic'), ('spectral', 'spectral'), ('spring', 'spring'), ('summer', 'summer'), ('terrain', 'terrain'), ('winter', 'winter')], max_length=200),
        ),
        migrations.AlterField(
            model_name='style',
            name='description',
            field=models.CharField(help_text='Descriptive name of this style, optional', blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='style',
            name='image_type',
            field=models.CharField(choices=[('filledcontours', 'filledcontours'), ('contours', 'contours'), ('pcolor', 'pcolor'), ('facets', 'facets'), ('composite', 'composite'), ('vectors', 'vectors'), ('barbs', 'barbs')], max_length=200, default='filledcontours'),
        ),
        migrations.AlterField(
            model_name='variable',
            name='default_max',
            field=models.FloatField(help_text='If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.', blank=True, null=True, default=None),
        ),
        migrations.AlterField(
            model_name='variable',
            name='default_min',
            field=models.FloatField(help_text='If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.', blank=True, null=True, default=None),
        ),
        migrations.AlterField(
            model_name='variable',
            name='logscale',
            field=models.NullBooleanField(help_text='If this variable should default to a log scale', default=None),
        ),
        migrations.AlterField(
            model_name='variable',
            name='std_name',
            field=models.CharField(help_text="The 'standard_name' of this variable", max_length=200),
        ),
        migrations.AlterField(
            model_name='variable',
            name='units',
            field=models.CharField(help_text="The 'units' of this variable", blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='default_max',
            field=models.FloatField(help_text='If no colorscalerange is specified, this is used for the max.  If None, autoscale is used.', blank=True, null=True, default=None),
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='default_min',
            field=models.FloatField(help_text='If no colorscalerange is specified, this is used for the min.  If None, autoscale is used.', blank=True, null=True, default=None),
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='description',
            field=models.CharField(help_text='Descriptive name of this layer, optional', blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='logscale',
            field=models.NullBooleanField(help_text='If this dataset variable should default to a log scale', default=None),
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='std_name',
            field=models.CharField(help_text="The 'standard_name' from the dataset variable", blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='units',
            field=models.CharField(help_text="The 'units' from the dataset variable", blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='virtuallayer',
            name='var_name',
            field=models.CharField(help_text='Variable name from dataset', max_length=200),
        ),
    ]
