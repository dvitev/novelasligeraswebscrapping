from os import name
from django.urls import path, include
from rest_framework import routers
from .viewsets import *

router = routers.DefaultRouter()
router.register('sitios', SitioViewSet, basename='sitios')
router.register('estructurasitios', EstructuraSitioViewSet, basename='estructurasitios')
router.register('novelas', NovelaViewSet, basename='novelas')
router.register('capitulos', CapituloViewSet, basename='capitulos')
router.register('contenidocapitulos', ContenidoCapituloViewSet, basename='contenidocapitulos')
# ...registrar las otras vistas similares

# urlpatterns = router.urls


urlpatterns = [
    path('', include(router.urls)),
    path('sitios/<int:pk>/',
         SitioViewSet.as_view({'get': 'retrieve'}), name='sitio-detail'),
    path('estructurasitios/<int:pk>/', EstructuraSitioViewSet.as_view(
        {'get': 'retrieve'}), name='estructurasitio-detail'),
    path('novelas/<int:pk>/',
         NovelaViewSet.as_view({'get': 'retrieve'}), name='novela-detail'),
    path('capitulos/<int:pk>/',
         CapituloViewSet.as_view({'get': 'retrieve'}), name='capitulo-detail'),
    path('contenidocapitulos/<int:pk>/', ContenidoCapituloViewSet.as_view(
        {'get': 'retrieve'}), name='contenidocapitulo-detail'),
]
