from django.urls import path
from .views_scraping import (
    IniciarScrapingView,
    ProgresoScrapingView,
    CancelarScrapingView,
    TareasActivasView,
)

urlpatterns = [
    path("iniciar/", IniciarScrapingView.as_view(), name="scraping-iniciar"),
    path("progreso/<str:task_id>/", ProgresoScrapingView.as_view(), name="scraping-progreso"),
    path("cancelar/<str:task_id>/", CancelarScrapingView.as_view(), name="scraping-cancelar"),
    path("tareas-activas/", TareasActivasView.as_view(), name="scraping-tareas-activas"),
]