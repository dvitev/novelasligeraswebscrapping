from rest_framework import serializers
from .models import *


class SitioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sitio
        fields = '__all__'


class EstructuraSitioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstructuraSitio
        fields = '__all__'


class NovelaSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Novela
        fields = '__all__'


class NovelaCapitulosConteoSerializer(serializers.Serializer):
    _id = serializers.CharField()
    nombre = serializers.CharField()
    sinopsis = serializers.CharField()
    autor = serializers.CharField()
    genero = serializers.CharField()
    status = serializers.CharField()
    url= serializers.URLField()
    imagen_url = serializers.URLField()
    cantidad_capitulos = serializers.IntegerField()
    cantidad_contenido_capitulos = serializers.IntegerField()


class GeneroSerializer(serializers.Serializer):
    generos = serializers.ListField(child=serializers.CharField(), allow_empty=True)


class CapituloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capitulo
        fields = '__all__'


class ContenidoCapituloSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContenidoCapitulo
        fields = '__all__'
