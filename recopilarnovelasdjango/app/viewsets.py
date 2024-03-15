from rest_framework import viewsets, generics
from rest_framework.response import Response
from bson.objectid import ObjectId
from .serializers import *
from .models import *


class SitioViewSet(viewsets.ModelViewSet):
    # queryset = Sitio.objects.all()
    serializer_class = SitioSerializer

    def get_queryset(self):
        return Sitio.objects.all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if 'pk' in kwargs:
            queryset = [Sitio.objects.get(_id=ObjectId(kwargs['pk']))]
        serializer = self.serializer_class(queryset, many=True).data
        
        return Response(serializer)



class EstructuraSitioViewSet(viewsets.ModelViewSet):
    # queryset = EstructuraSitio.objects.all()
    serializer_class = EstructuraSitioSerializer

    def get_queryset(self):
        return EstructuraSitio.objects.all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if 'pk' in kwargs:
            queryset = [EstructuraSitio.objects.get(_id=ObjectId(kwargs['pk']))]
        serializer = self.serializer_class(queryset, many=True).data
        return Response(serializer)


class NovelaViewSet(viewsets.ModelViewSet):
    # queryset = Novela.objects.all()
    serializer_class = NovelaSerializer
    
    def get_queryset(self):
        return Novela.objects.all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if 'pk' in kwargs:
            queryset = [Novela.objects.get(_id=ObjectId(kwargs['pk']))]
        serializer = self.serializer_class(queryset, many=True).data
        return Response(serializer)



class NovelaSitioViewSet(viewsets.ReadOnlyModelViewSet):
    # queryset = Novela.objects.all()
    serializer_class = NovelaSerializer

    def get_queryset(self):
        if 'pk' in self.kwargs:
            queryset = Novela.objects.filter(sitio_id=str(self.kwargs['pk']))
            return queryset
        else:
            return []

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True).data
        return Response(serializer)


class CapituloViewSet(viewsets.ModelViewSet):
    # queryset = Capitulo.objects.all()
    serializer_class = CapituloSerializer

    def get_queryset(self):
        return Capitulo.objects.all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if 'pk' in kwargs:
            queryset = [Capitulo.objects.get(_id=ObjectId(kwargs['pk']))]
        serializer = self.serializer_class(queryset, many=True).data
        return Response(serializer)


class CapituloNovelaViewSet(viewsets.ReadOnlyModelViewSet):
    # queryset = Novela.objects.all()
    serializer_class = NovelaSerializer

    def get_queryset(self):
        if 'pk' in self.kwargs:
            queryset = Capitulo.objects.filter(novela_id=str(self.kwargs['pk']))
            return queryset
        else:
            return []

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True).data
        return Response(serializer)


class ContenidoCapituloViewSet(viewsets.ModelViewSet):
    # queryset = ContenidoCapitulo.objects.all()
    serializer_class = ContenidoCapituloSerializer

    def get_queryset(self):
        return ContenidoCapitulo.objects.all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if 'pk' in kwargs:
            queryset = [ContenidoCapitulo.objects.get(_id=ObjectId(kwargs['pk']))]
        serializer = self.serializer_class(queryset, many=True).data
        return Response(serializer)
