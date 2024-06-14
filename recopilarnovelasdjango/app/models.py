from random import choices
# from django.db import models
from djongo import models
from djongo.models.fields import ObjectIdField

# Create your models here.


class Sitio(models.Model):
    class Idiomas(models.TextChoices):
        ESPANOL = 'es', 'Español'
        INGLES = 'en', 'Inglés'
        FRANCES = 'fr', 'Francés'
        ITALIANO = 'it', 'Italiano'
        ALEMAN = 'de', 'Alemán'
        PORTUGUES = 'pt', 'Portugués'
        KOREANO = 'ko', 'Koreano'
    
    _id = ObjectIdField()
    nombre = models.CharField(max_length=100, blank=True)
    url = models.URLField(max_length=200, blank=True)
    idioma = models.CharField(max_length=2, blank=True, choices=Idiomas.choices)
    objects = models.DjongoManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

def choice_sitio():
    return list(Sitio.objects.values_list('_id', 'nombre'))

class EstructuraSitio(models.Model):
    _id = ObjectIdField()
    sitio_id = models.CharField(max_length=100, blank=True)
    orden_selector = models.PositiveIntegerField(default=0)
    selector = models.CharField(max_length=100, blank=True)
    marcador = models.CharField(max_length=100, blank=True)
    tipo_selector = models.CharField(max_length=100, blank=True)
    nombre_selector = models.CharField(max_length=100, blank=True)
    objects = models.DjongoManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sitio_id} - {self.selector}"


class Novela(models.Model):
    class Status(models.TextChoices):
        EMISION = 'emision', 'Emisión'
        COMPLETO = 'completo', 'Completo'
        PAUSA = 'pausa', 'Pausado'
        ABANDONADO = 'abandonado', 'Abandonado'
    
    _id = ObjectIdField()
    sitio_id = models.CharField(max_length=100, blank=True)
    nombre = models.CharField(max_length=100, blank=True)
    sinopsis = models.TextField(blank=True)
    autor = models.CharField(max_length=100, blank=True)
    genero = models.TextField(blank=True)
    status = models.CharField(max_length=10, blank=True, choices=Status.choices)
    url = models.URLField(max_length=1000, blank=True)
    imagen_url = models.URLField(max_length=1000, blank=True)
    objects = models.DjongoManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} - {self.sitio_id}"
    

def choice_novela():
    return list(Novela.objects.values_list('_id', 'nombre'))


class Capitulo(models.Model):
    _id = ObjectIdField()
    novela_id = models.CharField(max_length=100, blank=True)
    nombre = models.TextField(blank=True)
    url = models.URLField(blank=True)
    objects = models.DjongoManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.novela_id} - {self.nombre}"


def choice_capitulo():
    return list(Capitulo.objects.values_list('_id', 'nombre'))

class ContenidoCapitulo(models.Model):
    _id = ObjectIdField()
    novela_id = models.CharField(max_length=100, blank=True)
    capitulo_id = models.CharField(max_length=100, blank=True)
    texto = models.TextField(blank=True)
    objects = models.DjongoManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.novela_id} - {self.capitulo_id} - {self.texto}"
