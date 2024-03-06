from rest_framework import serializers
from .models import *


class SitioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sitio
        fields = '__all__'
    
    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     representation['idioma'] = instance.get_idioma_display()
    #     return representation


class EstructuraSitioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstructuraSitio
        fields = '__all__'


class NovelaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Novela
        fields = '__all__'


class CapituloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capitulo
        fields = '__all__'


class ContenidoCapituloSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContenidoCapitulo
        fields = '__all__'
