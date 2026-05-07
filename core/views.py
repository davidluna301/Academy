from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.core.mail import send_mail
from django.db.models import Q
import csv
from io import BytesIO

from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ComentarioForm, DocenteRevisionForm, LoginForm, ProyectoForm, RegisterForm
from .models import Comentario, Proyecto

try:
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    canvas = None


def home(request: HttpRequest) -> HttpResponse:
    """
    Ruta raíz:
    - Si está autenticado, envía a la lista de items.
    - Si no, envía al login.
    """
    if request.user.is_authenticated:
        return redirect("proyecto_list")
    return redirect("login")


def login_view(request: HttpRequest) -> HttpResponse:
    """
    Login con formulario propio (no admin).
    """
    if request.user.is_authenticated:
        return redirect("proyecto_list")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            login(request, user)
            return redirect("proyecto_list")

    return render(request, "auth/login.html", {"form": form})


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Logout y redirección al login.
    """
    logout(request)
    return redirect("login")


def register_view(request: HttpRequest) -> HttpResponse:
    """
    Registro de usuario con validación de contraseña (UserCreationForm).
    """
    if request.user.is_authenticated:
        return redirect("proyecto_list")

    Group.objects.get_or_create(name="Estudiante")
    Group.objects.get_or_create(name="Docente")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cuenta creada correctamente. Ahora inicia sesión.")
        return redirect("login")

    return render(request, "auth/register.html", {"form": form})


def _es_docente(user: User) -> bool:
    return user.is_authenticated and user.groups.filter(name="Docente").exists()


class ProyectoQuerysetMixin:
    def get_queryset(self):
        qs = Proyecto.objects.select_related("estudiante").all()
        user = self.request.user
        if not _es_docente(user):
            qs = qs.filter(estudiante=user)
        estado = self.request.GET.get("estado")
        estudiante = self.request.GET.get("estudiante")
        if estado:
            qs = qs.filter(estado=estado)
        if estudiante and _es_docente(user):
            qs = qs.filter(Q(estudiante__username__icontains=estudiante) | Q(estudiante__email__icontains=estudiante))
        return qs


class ProyectoListView(LoginRequiredMixin, ProyectoQuerysetMixin, ListView):
    model = Proyecto
    template_name = "proyectos/list.html"
    context_object_name = "proyectos"


class ProyectoExportCsvView(LoginRequiredMixin, ProyectoQuerysetMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        proyectos = self.get_queryset()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="proyectos.csv"'
        writer = csv.writer(response)
        writer.writerow(["id", "titulo", "estudiante", "estado", "fecha_envio", "fecha_revision", "calificacion"])
        for p in proyectos:
            writer.writerow(
                [
                    p.id,
                    p.titulo,
                    p.estudiante.username,
                    p.estado,
                    p.fecha_envio.isoformat() if p.fecha_envio else "",
                    p.fecha_revision.isoformat() if p.fecha_revision else "",
                    str(p.calificacion) if p.calificacion is not None else "",
                ]
            )
        return response


class ProyectoExportPdfView(LoginRequiredMixin, ProyectoQuerysetMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if canvas is None:
            messages.error(request, "PDF no disponible: instala reportlab.")
            return redirect("proyecto_list")

        proyectos = self.get_queryset()
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        y = 800
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Academy - Proyectos")
        y -= 30
        p.setFont("Helvetica", 10)
        for pr in proyectos[:200]:
            linea = f"#{pr.id} | {pr.titulo} | {pr.estudiante.username} | {pr.estado} | {pr.calificacion or ''}"
            p.drawString(50, y, linea[:120])
            y -= 14
            if y < 60:
                p.showPage()
                y = 800
                p.setFont("Helvetica", 10)
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="proyectos.pdf")


class ProyectoCreateView(LoginRequiredMixin, CreateView):
    model = Proyecto
    form_class = ProyectoForm
    template_name = "proyectos/form.html"

    def dispatch(self, request, *args, **kwargs):
        if _es_docente(request.user):
            messages.error(request, "Los docentes no crean proyectos; revisan y aprueban.")
            return redirect("proyecto_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        proyecto = form.save(commit=False)
        proyecto.estudiante = self.request.user
        proyecto.save()
        messages.success(self.request, "Proyecto creado correctamente.")
        return redirect("proyecto_detail", pk=proyecto.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"title": "Nuevo proyecto", "submit_label": "Crear"})
        return ctx


class ProyectoOwnerOrDocenteMixin(UserPassesTestMixin):
    def test_func(self):
        proyecto = self.get_object()
        return _es_docente(self.request.user) or proyecto.estudiante_id == self.request.user.id


class ProyectoDetailView(LoginRequiredMixin, ProyectoQuerysetMixin, DetailView):
    model = Proyecto
    template_name = "proyectos/detail.html"
    context_object_name = "proyecto"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        proyecto: Proyecto = ctx["proyecto"]
        ctx["es_docente"] = _es_docente(self.request.user)
        ctx["comentario_form"] = ComentarioForm()
        ctx["revision_form"] = DocenteRevisionForm(instance=proyecto) if _es_docente(self.request.user) else None
        return ctx


class ProyectoUpdateView(LoginRequiredMixin, ProyectoOwnerOrDocenteMixin, UpdateView):
    model = Proyecto
    form_class = ProyectoForm
    template_name = "proyectos/form.html"

    def dispatch(self, request, *args, **kwargs):
        proyecto = self.get_object()
        if _es_docente(request.user):
            messages.error(request, "Los docentes no editan contenido del proyecto (solo estado/calificación).")
            return redirect("proyecto_detail", pk=proyecto.pk)
        if proyecto.estudiante_id != request.user.id:
            messages.error(request, "No tienes permisos para editar este proyecto.")
            return redirect("proyecto_list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"title": "Editar proyecto", "submit_label": "Guardar"})
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Cambios guardados.")
        return reverse("proyecto_detail", kwargs={"pk": self.object.pk})


class ProyectoDeleteView(LoginRequiredMixin, ProyectoOwnerOrDocenteMixin, DeleteView):
    model = Proyecto
    template_name = "proyectos/confirm_delete.html"
    context_object_name = "proyecto"

    def dispatch(self, request, *args, **kwargs):
        proyecto = self.get_object()
        if _es_docente(request.user):
            messages.error(request, "Los docentes no eliminan proyectos.")
            return redirect("proyecto_detail", pk=proyecto.pk)
        if proyecto.estudiante_id != request.user.id:
            messages.error(request, "No tienes permisos para eliminar este proyecto.")
            return redirect("proyecto_list")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Proyecto eliminado.")
        return reverse("proyecto_list")


class DocenteRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return _es_docente(self.request.user)


class ProyectoRevisionUpdateView(LoginRequiredMixin, DocenteRequiredMixin, UpdateView):
    model = Proyecto
    form_class = DocenteRevisionForm
    template_name = "proyectos/revision_form.html"

    def form_valid(self, form):
        proyecto = form.save(commit=False)
        proyecto.fecha_revision = timezone.now()
        proyecto.save()
        messages.success(self.request, "Revisión actualizada.")
        return redirect("proyecto_detail", pk=proyecto.pk)


class ComentarioCreateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        proyecto = get_object_or_404(Proyecto, pk=pk)
        if not (_es_docente(request.user) or proyecto.estudiante_id == request.user.id):
            messages.error(request, "No tienes permisos para comentar en este proyecto.")
            return redirect("proyecto_list")
        if proyecto.comentarios_bloqueados:
            messages.error(request, "Este proyecto está aprobado; no se permiten nuevos comentarios.")
            return redirect("proyecto_detail", pk=pk)

        form = ComentarioForm(request.POST)
        if not form.is_valid():
            messages.error(request, "No se pudo guardar el comentario.")
            return redirect("proyecto_detail", pk=pk)

        comentario = form.save(commit=False)
        comentario.proyecto = proyecto
        comentario.usuario = request.user
        comentario.save()

        # Notificación por correo al estudiante
        if proyecto.estudiante.email:
            send_mail(
                subject=f"[Academy] Nuevo comentario: {proyecto.titulo}",
                message=(
                    f"Hola {proyecto.estudiante.username},\n\n"
                    f"Se ha agregado un comentario a tu proyecto \"{proyecto.titulo}\":\n\n"
                    f"{comentario.texto}\n\n"
                    "Ingresa a Academy para revisarlo."
                ),
                from_email=None,
                recipient_list=[proyecto.estudiante.email],
                fail_silently=True,
            )

        messages.success(request, "Comentario enviado.")
        return redirect("proyecto_detail", pk=pk)
