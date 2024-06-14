from os import name
from django.urls import path, include
from rest_framework import routers
from .viewsets import *
from .views import generar_pdf

router = routers.DefaultRouter()
router.register('sitios', SitioViewSet, basename='sitios')
router.register('estructurasitios', EstructuraSitioViewSet,
                basename='estructurasitios')
router.register('novelas', NovelaViewSet, basename='novelas')
router.register('novelassitio', NovelaSitioViewSet, basename='novelassitio')
router.register('capitulos', CapituloViewSet, basename='capitulos')
router.register('capitulosnovela',CapituloNovelaViewSet, basename='capitulosnovela')
router.register('contenidocapitulos', ContenidoCapituloViewSet,
                basename='contenidocapitulos')
router.register('generos', GeneroViewSet, basename='generos')
# ...registrar las otras vistas similares

# urlpatterns = router.urls


urlpatterns = [
    path('', include(router.urls)),
    path('generar_pdf/<str:novela_id>/', generar_pdf, name='generar_pdf'),
]
