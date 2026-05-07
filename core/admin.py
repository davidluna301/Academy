from django.contrib import admin

from .models import Comentario, Proyecto


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "estudiante", "estado", "fecha_envio", "fecha_revision", "calificacion")
    list_filter = ("estado",)
    search_fields = ("titulo", "estudiante__username", "estudiante__email")
    list_select_related = ("estudiante",)


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ("id", "proyecto", "usuario", "fecha")
    search_fields = ("proyecto__titulo", "usuario__username", "usuario__email")
    list_select_related = ("proyecto", "usuario")
