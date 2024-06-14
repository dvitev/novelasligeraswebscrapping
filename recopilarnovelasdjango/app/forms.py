from django import forms
from .models import *


class EstructuraSitioForm(forms.ModelForm):
    sitio_id = forms.ChoiceField(choices=choice_sitio)

    class Meta:
        model = EstructuraSitio
        fields = ['sitio_id', 'orden_selector', 'selector',
                  'marcador', 'tipo_selector', 'nombre_selector']


class NovelaForm(forms.ModelForm):
    sitio_id = forms.ChoiceField(choices=choice_sitio)

    class Meta:
        model = Novela
        fields = ['sitio_id', 'nombre', 'sinopsis', 'autor',
                  'genero', 'status', 'url', 'imagen_url']


class CapituloForm(forms.ModelForm):
    novela_id = forms.ChoiceField(choices=choice_novela)

    class Meta:
        model = Capitulo
        fields = ['novela_id', 'nombre', 'url']


class ContenidoCapituloForm(forms.ModelForm):
    novela_id = forms.ChoiceField(choices=choice_novela)
    Capitulo_id = forms.ChoiceField(choices=choice_capitulo)

    class Meta:
        model = ContenidoCapitulo
        fields = ['novela_id', 'capitulo_id', 'texto']
