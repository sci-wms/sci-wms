'''
Created on Sep 6, 2011

@author: ACrosby
'''
from fvcom_compute.fvcom_stovepipe.models import Node, Cell, Time, Level
from django.contrib import admin

admin.site.register(Node)
admin.site.register(Cell)
admin.site.register(Time)
admin.site.register(Level)