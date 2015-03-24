'''
Created on Feb 12, 2015

@author: ayan
'''
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from sciwms.apps.wms.models import Dataset, VirtualLayer
from serializers import DatasetSerializer, VirtualLayerSerializer


class DatasetList(ListCreateAPIView):
    """
    Get a list of Sci-WMS datasets.
    Supports GET and POST methods.
    
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    
    
class DatasetDetail(RetrieveUpdateDestroyAPIView):
    """
    Get or update a specific Sci-WMS dataset.
    Supports GET, PUT, DELETE, and PATCH methods.
    
    A DELETE on a dataset with a defined m2m relationship
    to another table will also delete that relationship.
    
    PUT and PATCH requests with a defined m2m relations
    to another table will be updated accordingly.
    
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer


class VirtualLayerList(ListCreateAPIView):
    """
    Get a list of virtual layers in Sci-WMS.
    Supports GET and POST methods.
    
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = VirtualLayer.objects.all()
    serializer_class = VirtualLayerSerializer
    
    
class VirtualLayerDetail(RetrieveUpdateDestroyAPIView):
    """
    Get or update a specific virtual layer in Sci-WMS
    Supports GET, PUT, DELETE, and PATCH methods.
    
    A DELETE on a dataset with a defined m2m relationship
    to another table will also delete that relationship.
    
    PUT and PATCH requests with a defined m2m relations
    to another table will be updated accordingly.
    
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = VirtualLayer.objects.all()
    serializer_class= VirtualLayerSerializer