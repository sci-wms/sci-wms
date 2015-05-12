# -*- coding: utf-8 -*-
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from wms.models import Dataset
from serializers import DatasetSerializer, SGridDatasetSerializer, UGridDatasetSerializer
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404


class DatasetList(APIView):
    """
    List all snippets, or create a new snippet.
    """
    def get(self, request, format=None):
        snippets = Dataset.objects.select_related('layer_set__styles').all()
        serializer = DatasetSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        if 'ugrid' in request.data['type']:
            request.data['type'] = 'wms.ugriddataset'
            serializer = UGridDatasetSerializer(data=request.data)
        elif 'sgrid' in request.data['type']:
            request.data['type'] = 'wms.sgriddataset'
            serializer = SGridDatasetSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DatasetDetail(APIView):
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

    def get_object(self, pk):
        try:
            return Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        dataset = self.get_object(pk)
        serializer = DatasetSerializer(dataset)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        dataset = self.get_object(pk)
        if 'ugrid' in request.data['type']:
            request.data['type'] = 'wms.ugriddataset'
            serializer = UGridDatasetSerializer(dataset, data=request.data)
        elif 'sgrid' in request.data['type']:
            request.data['type'] = 'wms.sgriddataset'
            serializer = SGridDatasetSerializer(dataset, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        dataset = self.get_object(pk)
        dataset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
