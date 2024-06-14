from django.contrib import admin
from .models import *
from .forms import *
from import_export import resources
from import_export.admin import ImportExportModelAdmin


MyResorcesAdmin = lambda model: type('subclass' + model.__name__, (resources.MdelResources,), {
    'Meta': model._meta.model
})

class SitioAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [x.name for x in Sitio._meta.fields]
    search_field = [x.name for x in Sitio._meta.fields]
    list_filter = ['idioma']
    resource_class = MyResorcesAdmin
    readonly_fields = ['created_at', 'updated_at']

class EstructuraSitioAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [x.name for x in EstructuraSitio._meta.fields]
    search_field = ['selector','tipo_selector']
    list_filter = ['sitio_id','tipo_selector']
    form = EstructuraSitioForm
    resource_class = MyResorcesAdmin
    readonly_fields = ['created_at', 'updated_at']

class NovelaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [x.name for x in Novela._meta.fields]
    search_field = [x.name for x in Novela._meta.fields]
    list_filter = ['sitio_id','status']
    form = NovelaForm
    resource_class = MyResorcesAdmin
    readonly_fields = ['created_at', 'updated_at']

class CapituloAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [x.name for x in Capitulo._meta.fields]
    search_field = [x.name for x in Capitulo._meta.fields]
    list_filter = ['novela_id']
    form = CapituloForm
    resource_class = MyResorcesAdmin
    readonly_fields = ['created_at', 'updated_at']

class ContenidoCapituloAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [x.name for x in ContenidoCapitulo._meta.fields]
    search_field = [x.name for x in ContenidoCapitulo._meta.fields]
    list_filter = ['capitulo_id']
    form = ContenidoCapituloForm
    resource_class = MyResorcesAdmin
    readonly_fields = ['created_at', 'updated_at']


# Register your models here.
admin.site.register(Sitio, SitioAdmin)
admin.site.register(EstructuraSitio, EstructuraSitioAdmin)
admin.site.register(Novela, NovelaAdmin)
admin.site.register(Capitulo, CapituloAdmin)
admin.site.register(ContenidoCapitulo, ContenidoCapituloAdmin)