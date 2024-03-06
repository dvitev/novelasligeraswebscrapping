from rest_framework import viewsets
from rest_framework.response import Response
from bson.objectid import ObjectId
from .serializers import *
from .models import *


class SitioViewSet(viewsets.ModelViewSet):
    queryset = Sitio.objects.all()
    serializer_class = SitioSerializer

    def retrieve(self, request, pk=None):
        try:
            sitio = Sitio.objects.get(_id=ObjectId(pk))
            serializer = SitioSerializer(sitio)
            return Response(serializer.data)
        except Sitio.DoesNotExist:
            return Response(status=404)


class EstructuraSitioViewSet(viewsets.ModelViewSet):
    queryset = EstructuraSitio.objects.all()
    serializer_class = EstructuraSitioSerializer

    def retrieve(self, request, *args, **kwargs):
        # The Primary Key of the object is passed to the retrieve method through self.kwargs
        object_id = self.kwargs['pk']


class NovelaViewSet(viewsets.ModelViewSet):
    queryset = Novela.objects.all()
    serializer_class = NovelaSerializer

    def retrieve(self, request, pk=None):
        try:
            novela = Novela.objects.get(_id=ObjectId(pk))
            serializer = NovelaSerializer(novela)
            return Response(serializer.data)
        except Sitio.DoesNotExist:
            return Response(status=404)


class NovelaSitioViewSet(viewsets.ModelViewSet):
    # queryset = Novela.objects.all()
    serializer_class = NovelaSerializer

    def retrieve(self, request, sitio_id=None):
        try:
            novela = Novela.objects.get(sitio_id=str(sitio_id))
            serializer = self.serializer_class(novela, many=True)
            return Response(serializer.data)
        except Sitio.DoesNotExist:
            return Response(status=404)


class CapituloViewSet(viewsets.ModelViewSet):
    queryset = Capitulo.objects.all()
    serializer_class = CapituloSerializer

    def retrieve(self, request, *args, **kwargs):
        # The Primary Key of the object is passed to the retrieve method through self.kwargs
        object_id = self.kwargs['pk']


class ContenidoCapituloViewSet(viewsets.ModelViewSet):
    queryset = ContenidoCapitulo.objects.all()
    serializer_class = ContenidoCapituloSerializer

    def retrieve(self, request, *args, **kwargs):
        # The Primary Key of the object is passed to the retrieve method through self.kwargs
        object_id = self.kwargs['pk']
