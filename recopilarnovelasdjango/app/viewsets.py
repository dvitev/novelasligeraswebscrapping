from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.core.cache import cache
from .serializers import *
from .repositories import (
    SitioRepository,
    NovelaRepository,
    CapituloRepository,
    ContenidoRepository,
)
import logging

logger = logging.getLogger('app')

sitio_repo = SitioRepository()
novela_repo = NovelaRepository()
capitulo_repo = CapituloRepository()
contenido_repo = ContenidoRepository()


def cache_response(timeout=300):
    def decorator(view_func):
        def wrapper(self, request, *args, **kwargs):
            cache_key = f"{request.path}:{request.query_params}"
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response(cached_data)
            response = view_func(self, request, *args, **kwargs)
            if response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
            return response
        return wrapper
    return decorator


class SitioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SitioSerializer

    def list(self, request, *args, **kwargs):
        sitios = sitio_repo.find_all_sitios()
        serializer = self.serializer_class(sitios, many=True)
        return Response(serializer.data)

    @cache_response(300)
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        sitio = sitio_repo.find_sitio_by_id(pk)
        if not sitio:
            return Response({'error': 'Sitio no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class([sitio], many=True)
        return Response(serializer.data)


class EstructuraSitioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EstructuraSitioSerializer

    def list(self, request, *args, **kwargs):
        return Response([])

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        sitio = sitio_repo.find_sitio_by_id(pk)
        if not sitio:
            return Response({'error': 'Estructura Sitio no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        estructura = {
            'estructura': sitio.get('estructura', {})
        }
        serializer = self.serializer_class(data=estructura)
        serializer.is_valid()
        return Response(serializer.data)


class NovelaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NovelaSerializer

    def list(self, request, *args, **kwargs):
        return Response([])

    @cache_response(300)
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        novela = novela_repo.find_novela_by_id(pk)
        if not novela:
            return Response({'error': 'Novela no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class([novela], many=True)
        return Response(serializer.data)


class NovelaPagination(PageNumberPagination):
    page_size = 100


class NovelaSitioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NovelaSerializer
    pagination_class = NovelaPagination

    def list(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            return Response([])

        queryset = novela_repo.find_novelas_by_sitio(pk, exclude_genres=True)

        if 'page' not in request.query_params:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        return super().list(request, *args, **kwargs)

    @cache_response(300)
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        novela = novela_repo.find_novela_by_id(pk)
        if not novela:
            return Response({'error': 'Novela no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class([novela], many=True)
        return Response(serializer.data)


class NovelaCapitulosConteoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NovelaCapitulosConteoSerializer

    @cache_response(300)
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        novela_data = novela_repo.get_conteo_novela_aggregate(pk)
        if not novela_data:
            return Response({'error': 'Novela no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        titulo = novela_data.get('titulo') or novela_data.get('nombre') or ''
        data = {
            '_id': str(novela_data.get('_id', '')),
            'nombre': titulo,
            'titulo': titulo,
            'sinopsis': novela_data.get('sinopsis', ''),
            'autor': novela_data.get('autor', ''),
            'genero': novela_data.get('genero', ''),
            'status': novela_data.get('status', ''),
            'url': novela_data.get('url', ''),
            'imagen_url': novela_data.get('imagen_url', ''),
            'cantidad_capitulos': novela_data.get('cantidad_capitulos', 0),
            'cantidad_contenido_capitulos': novela_data.get('cantidad_contenido_capitulos', 0)
        }

        serializer = self.serializer_class(data=data)
        serializer.is_valid()
        return Response(serializer.data)


class CapituloViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CapituloSerializer

    def list(self, request, *args, **kwargs):
        return Response([])

    @cache_response(300)
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        capitulo = capitulo_repo.find_capitulo_by_id(pk)
        if not capitulo:
            return Response({'error': 'Capítulo no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class([capitulo], many=True)
        return Response(serializer.data)


class CapituloNovelaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CapituloSerializer

    def list(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            return Response([])

        capitulos = capitulo_repo.find_capitulos_by_novela(pk, sort_order=1)
        serializer = self.serializer_class(capitulos, many=True)
        return Response(serializer.data)

    @cache_response(300)
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        capitulo = capitulo_repo.find_capitulo_by_id(pk)
        if not capitulo:
            return Response({'error': 'Capítulo no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class([capitulo], many=True)
        return Response(serializer.data)


class ContenidoCapituloViewSet(viewsets.ModelViewSet):
    serializer_class = ContenidoCapituloSerializer

    def list(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            return Response([])

        contenidos = contenido_repo.find_contenidos_by_capitulo(pk)
        serializer = self.serializer_class(contenidos, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        contenido = contenido_repo.find_contenido_by_capitulo(pk)
        if not contenido:
            return Response({'error': 'Contenido no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class([contenido], many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data
        contenido_id = contenido_repo.create_contenido(data)
        return Response({'_id': contenido_id}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        updated = contenido_repo.update_contenido(pk, request.data)
        if not updated:
            return Response({'error': 'Contenido no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'status': 'updated'})

    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        deleted = contenido_repo.delete_contenido(pk)
        if not deleted:
            return Response({'error': 'Contenido no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GeneroViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GeneroSerializer

    def list(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            return Response({'generos': []})

        generos = novela_repo.get_generos_by_sitio_aggregate(pk)
        serializer = self.serializer_class(data={'generos': generos})
        serializer.is_valid()
        return Response(serializer.data)

    @cache_response(300)
    def retrieve(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)