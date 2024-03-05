from rest_framework import viewsets
from .serializers import *
from .models import *

class SitioViewSet(viewsets.ModelViewSet):
    queryset = Sitio.objects.all()
    serializer_class = SitioSerializer


class EstructuraSitioViewSet(viewsets.ModelViewSet):
    queryset = EstructuraSitio.objects.all()
    serializer_class = EstructuraSitioSerializer


class NovelaViewSet(viewsets.ModelViewSet):
    queryset = Novela.objects.all()
    serializer_class = NovelaSerializer


class CapituloViewSet(viewsets.ModelViewSet):
    queryset = Capitulo.objects.all()
    serializer_class = CapituloSerializer


class ContenidoCapituloViewSet(viewsets.ModelViewSet):
    queryset = ContenidoCapitulo.objects.all()
    serializer_class = ContenidoCapituloSerializer


