# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0008_auto_20150428_2136'),
    ]

    operations = [
        migrations.AddField(
            model_name='style',
            name='colormap',
            field=models.CharField(help_text=b'The matplotlib colormaps. See: http://matplotlib.org/1.2.1/examples/pylab_examples/show_colormaps.html.', max_length=200, choices=[('Accent', 'Accent'), ('Blues', 'Blues'), ('BrBG', 'BrBG'), ('BuGn', 'BuGn'), ('BuPu', 'BuPu'), ('CMRmap', 'CMRmap'), ('Dark2', 'Dark2'), ('GnBu', 'GnBu'), ('Greens', 'Greens'), ('Greys', 'Greys'), ('OrRd', 'OrRd'), ('Oranges', 'Oranges'), ('PRGn', 'PRGn'), ('Paired', 'Paired'), ('Pastel1', 'Pastel1'), ('Pastel2', 'Pastel2'), ('PiYG', 'PiYG'), ('PuBu', 'PuBu'), ('PuBuGn', 'PuBuGn'), ('PuOr', 'PuOr'), ('PuRd', 'PuRd'), ('Purples', 'Purples'), ('RdBu', 'RdBu'), ('RdGy', 'RdGy'), ('RdPu', 'RdPu'), ('RdYlBu', 'RdYlBu'), ('RdYlGn', 'RdYlGn'), ('Reds', 'Reds'), ('Set1', 'Set1'), ('Set2', 'Set2'), ('Set3', 'Set3'), ('Spectral', 'Spectral'), ('Wistia', 'Wistia'), ('YlGn', 'YlGn'), ('YlGnBu', 'YlGnBu'), ('YlOrBr', 'YlOrBr'), ('YlOrRd', 'YlOrRd'), ('afmhot', 'afmhot'), ('autumn', 'autumn'), ('binary', 'binary'), ('bone', 'bone'), ('brg', 'brg'), ('bwr', 'bwr'), ('cool', 'cool'), ('coolwarm', 'coolwarm'), ('copper', 'copper'), ('cubehelix', 'cubehelix'), ('flag', 'flag'), ('gist_earth', 'gist_earth'), ('gist_gray', 'gist_gray'), ('gist_heat', 'gist_heat'), ('gist_ncar', 'gist_ncar'), ('gist_rainbow', 'gist_rainbow'), ('gist_stern', 'gist_stern'), ('gist_yarg', 'gist_yarg'), ('gnuplot', 'gnuplot'), ('gnuplot2', 'gnuplot2'), ('gray', 'gray'), ('hot', 'hot'), ('hsv', 'hsv'), ('jet', 'jet'), ('nipy_spectral', 'nipy_spectral'), ('ocean', 'ocean'), ('pink', 'pink'), ('prism', 'prism'), ('rainbow', 'rainbow'), ('seismic', 'seismic'), ('spectral', 'spectral'), ('spring', 'spring'), ('summer', 'summer'), ('terrain', 'terrain'), ('winter', 'winter')]),
            preserve_default=True,
        ),
    ]
