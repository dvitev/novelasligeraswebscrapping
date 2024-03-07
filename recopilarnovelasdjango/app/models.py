from random import choices
# from django.db import models
from djongo import models
from djongo.models.fields import ObjectIdField

# Create your models here.


class Sitio(models.Model):
    _id = models.ObjectIdField()
    nombre = models.CharField(max_length=100, blank=True)
    url = models.CharField(max_length=100, blank=True)
    idioma = models.CharField(max_length=100, blank=True, choices=(
        ('es', 'Español'),
        ('en', 'Inglés'),
        ('fr', 'Francés'),
        ('it', 'Italiano'),
        ('de', 'Alemán'),
        ('pt', 'Portugués'),
        ('ko', 'Koreano'),
    ))
    objects = models.DjongoManager()

    def __str__(self):
        return self.nombre

def choise_sitio():
        sitios = Sitio.objects.all().values()
        choises =[(str(x['_id']), x['nombre']) for x in sitios]
        # print(choises)
        return choises

class EstructuraSitio(models.Model):
    _id = models.ObjectIdField()
    sitio_id = models.CharField(max_length=100, blank=True, choices=choise_sitio())
    orden_selector = models.PositiveIntegerField(default=0)
    selector = models.CharField(max_length=100, blank=True)
    marcador = models.CharField(max_length=100, blank=True)
    tipo_selector = models.CharField(max_length=100, blank=True)
    nombre_selector = models.CharField(max_length=100, blank=True)
    objects = models.DjongoManager()


class Novela(models.Model):
    _id = models.ObjectIdField()
    sitio_id = models.CharField(max_length=100, blank=True, choices=choise_sitio())
    nombre = models.CharField(max_length=100, blank=True)
    sinopsis = models.TextField(blank=True)
    autor = models.CharField(max_length=100, blank=True)
    genero = models.TextField(blank=True)
    status = models.CharField(max_length=100, blank=True, choices=(
        ('emision', 'Emision'),
        ('completo', 'Completo'),
        ('pausa', 'Pausado'),
        ('abandonado', 'Abandonado'),
    ))
    url = models.CharField(max_length=1000)
    imagen_url = models.CharField(max_length=1000, blank=True)
    objects = models.DjongoManager()

    def __str__(self):
        return f"{self.nombre} - {self.sitio_id}"
    

def choise_novela():
        sitios = Novela.objects.all().values()
        choises =[(str(x['_id']), x['nombre']) for x in sitios]
        # print(choises)
        return choises


class Capitulo(models.Model):
    _id = models.ObjectIdField()
    novela_id = models.CharField(max_length=100, blank=True, choices=choise_novela())
    nombre = models.TextField(blank=True)
    url = models.TextField(blank=True)
    objects = models.DjongoManager()

    def __str__(self):
        return f"{self.novela} - {self.nombre}"


def choise_capitulo():
    capitulos = Capitulo.objects.all().values()
    choises = [(str(x['_id']), x['nombre']) for x in capitulos]
    return choises

class ContenidoCapitulo(models.Model):
    _id = models.ObjectIdField()
    novela_id = models.CharField(max_length=100, blank=True, choices=choise_novela())
    capitulo_id = models.CharField(max_length=100, blank=True, choices=choise_capitulo())
    texto = models.TextField(blank=True)
    objects = models.DjongoManager()

    def __str__(self):
        return f"{self.capitulo_id} - {self.texto}"
