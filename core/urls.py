from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    # Auth
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Proyectos
    path("proyectos/", views.ProyectoListView.as_view(), name="proyecto_list"),
    path("proyectos/export/csv/", views.ProyectoExportCsvView.as_view(), name="proyecto_export_csv"),
    path("proyectos/export/pdf/", views.ProyectoExportPdfView.as_view(), name="proyecto_export_pdf"),
    path("proyectos/new/", views.ProyectoCreateView.as_view(), name="proyecto_create"),
    path("proyectos/<int:pk>/", views.ProyectoDetailView.as_view(), name="proyecto_detail"),
    path("proyectos/<int:pk>/edit/", views.ProyectoUpdateView.as_view(), name="proyecto_update"),
    path("proyectos/<int:pk>/delete/", views.ProyectoDeleteView.as_view(), name="proyecto_delete"),
    path("proyectos/<int:pk>/revision/", views.ProyectoRevisionUpdateView.as_view(), name="proyecto_revision"),
    path("proyectos/<int:pk>/comentarios/new/", views.ComentarioCreateView.as_view(), name="comentario_create"),
]

