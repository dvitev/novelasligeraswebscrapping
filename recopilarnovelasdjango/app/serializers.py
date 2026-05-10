from rest_framework import serializers


class SitioSerializer(serializers.Serializer):
    _id = serializers.CharField(required=False)
    nombre = serializers.CharField()
    url = serializers.CharField(required=False)
    estructura = serializers.DictField(required=False)


class EstructuraSitioSerializer(serializers.Serializer):
    estructura = serializers.DictField(required=False)


class GeneroField(serializers.Field):
    def to_representation(self, value):
        if isinstance(value, list):
            return ", ".join(value)
        return value or ""
    
    def to_internal_value(self, data):
        if isinstance(data, list):
            return data
        if isinstance(data, str):
            return [g.strip() for g in data.split(",") if g.strip()]
        return []


class NovelaSerializer(serializers.Serializer):
    _id = serializers.CharField(required=False)
    titulo = serializers.CharField(required=False)
    nombre = serializers.CharField(required=False)
    sinopsis = serializers.CharField(required=False, allow_blank=True)
    autor = serializers.CharField(required=False, allow_blank=True)
    genero = GeneroField(required=False)
    generos = GeneroField(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    url = serializers.CharField(required=False, allow_blank=True)
    imagen_url = serializers.CharField(required=False, allow_blank=True)
    sitio_id = serializers.CharField(required=False)
    cantidad_capitulos = serializers.IntegerField(required=False)


class NovelaCapitulosConteoSerializer(serializers.Serializer):
    _id = serializers.CharField()
    nombre = serializers.CharField(required=False)
    titulo = serializers.CharField(required=False)
    sinopsis = serializers.CharField(required=False, allow_blank=True)
    autor = serializers.CharField(required=False, allow_blank=True)
    genero = GeneroField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    url = serializers.CharField(required=False, allow_blank=True)
    imagen_url = serializers.CharField(required=False, allow_blank=True)
    cantidad_capitulos = serializers.IntegerField()
    cantidad_contenido_capitulos = serializers.IntegerField()


class GeneroSerializer(serializers.Serializer):
    generos = serializers.ListField(child=serializers.CharField(), allow_empty=True)


class CapituloSerializer(serializers.Serializer):
    _id = serializers.CharField(required=False)
    novela_id = serializers.CharField()
    numero = serializers.IntegerField()
    titulo = serializers.CharField(required=False, allow_blank=True)
    url = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(required=False)


class ContenidoCapituloSerializer(serializers.Serializer):
    _id = serializers.CharField(required=False)
    novela_id = serializers.CharField(required=False)
    capitulo_id = serializers.CharField()
    contenido = serializers.CharField(required=False, allow_blank=True)
    traduccion = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(required=False)