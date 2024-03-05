from random import choices
from django.db import models

# Create your models here.


class Sitio(models.Model):
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

    def __str__(self):
        return self.nombre


class EstructuraSitio(models.Model):
    sitio = models.ForeignKey(Sitio, on_delete=models.CASCADE)
    orden_selector = models.PositiveIntegerField(default=0)
    selector = models.CharField(max_length=100, blank=True)
    marcador = models.CharField(max_length=100, blank=True)
    tipo_selector = models.CharField(max_length=100, blank=True)
    nombre_selector = models.CharField(max_length=100, blank=True)


class Novela(models.Model):
    sitio = models.ForeignKey(Sitio, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"{self.nombre} - {self.sitio}"


class Capitulo(models.Model):
    novela = models.ForeignKey(Novela, on_delete=models.CASCADE)
    nombre = models.TextField(blank=True)
    url = models.TextField(blank=True)

    def __str__(self):
        return f"{self.novela} - {self.nombre}"


class ContenidoCapitulo(models.Model):
    capitulo = models.ForeignKey(Capitulo, on_delete=models.CASCADE)
    texto = models.TextField(blank=True)

    def __str__(self):
        return f"{self.capitulo} - {self.texto}"
