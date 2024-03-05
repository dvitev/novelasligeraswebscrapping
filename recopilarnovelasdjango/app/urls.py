from django.urls import path, include
from rest_framework import routers
from .viewsets import *
        
router = routers.DefaultRouter()
router.register('sitios', SitioViewSet)
router.register('estructurasitios', EstructuraSitioViewSet)
router.register('novelas', NovelaViewSet)
router.register('capitulos', CapituloViewSet)
router.register('contenidocapitulos', ContenidoCapituloViewSet)
# ...registrar las otras vistas similares

urlpatterns = router.urls