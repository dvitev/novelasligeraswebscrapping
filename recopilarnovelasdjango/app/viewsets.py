from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from bson.objectid import ObjectId
from .serializers import *
from .models import *


class SitioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SitioSerializer

    def get_queryset(self):
        return Sitio.objects.all()

    def retrieve(self, request, *args, **kwargs):
        obj = get_object_or_404(Sitio, _id=ObjectId(kwargs['pk']))
        serializer = self.serializer_class(obj)
        return Response(serializer.data)



class EstructuraSitioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EstructuraSitioSerializer

    def get_queryset(self):
        return EstructuraSitio.objects.all()

    def retrieve(self, request, *args, **kwargs):
        obj = get_object_or_404(EstructuraSitio, _id=ObjectId(kwargs['pk']))
        serializer = self.serializer_class(obj)
        return Response(serializer.data)


class NovelaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NovelaSerializer
    
    def get_queryset(self):
        return Novela.objects.all()

    def retrieve(self, request, *args, **kwargs):
        obj = get_object_or_404(Novela, _id=ObjectId(kwargs['pk']))
        serializer = self.serializer_class(obj)
        return Response(serializer.data)



class NovelaSitioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NovelaSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if pk:
            queryset_list = []
            queryset = Novela.objects.filter(sitio_id=pk)
            for novela in queryset:
                if 'Yaoi' not in novela.genero and 'Lgbt+' not in novela.genero and 'Yuri' not in novela.genero and 'Shounen ai' not in novela.genero and 'Shoujo ai' not in novela.genero:
                    queryset_list.append(novela)
            return queryset_list
        return Novela.objects.none()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class CapituloViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CapituloSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if pk:
            return Capitulo.objects.filter(_id=pk)
        return Capitulo.objects.none()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class CapituloNovelaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CapituloSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if pk:
            return Capitulo.objects.filter(novela_id=pk)
        return Capitulo.objects.none()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class ContenidoCapituloViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContenidoCapituloSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if pk:
            return ContenidoCapitulo.objects.filter(capitulo_id=pk)
        return ContenidoCapitulo.objects.none()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class GeneroViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GeneroSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        # Obtener todos los géneros de la base de datos
        if pk:
            return Novela.objects.filter(sitio_id=pk)
        return Novela.objects.none()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        generos_list = set(genero.strip() for novela in queryset for genero in novela.genero.split(',') if genero.strip() not in ['Yaoi', 'Lgbt+', 'Yuri', 'Shounen ai', 'Shoujo ai'])
        generos_list = sorted(generos_list)
        serializer = self.serializer_class(data={'generos': generos_list})
        serializer.is_valid()
        return Response(serializer.data)