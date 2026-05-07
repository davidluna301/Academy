from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.utils import timezone

from .models import Comentario, Proyecto


@dataclass(frozen=True)
class DemoUser:
    username: str
    email: str
    password: str
    group: str


DEMO_USERS: list[DemoUser] = [
    DemoUser(username="docente1", email="docente1@academy.test", password="Docente123!", group="Docente"),
    DemoUser(username="estudiante1", email="estudiante1@academy.test", password="Estudiante123!", group="Estudiante"),
    DemoUser(username="estudiante2", email="estudiante2@academy.test", password="Estudiante123!", group="Estudiante"),
]


def seed_demo_data() -> None:
    g_est, _ = Group.objects.get_or_create(name="Estudiante")
    g_doc, _ = Group.objects.get_or_create(name="Docente")

    users: dict[str, User] = {}
    for du in DEMO_USERS:
        user, created = User.objects.get_or_create(username=du.username, defaults={"email": du.email})
        if created:
            user.set_password(du.password)
            user.email = du.email
            user.save()
        # Asegura grupo
        if du.group == "Docente":
            user.groups.add(g_doc)
        else:
            user.groups.add(g_est)
        users[du.username] = user

    # Proyectos para estudiantes
    e1 = users["estudiante1"]
    e2 = users["estudiante2"]
    d1 = users["docente1"]

    p1, _ = Proyecto.objects.get_or_create(
        estudiante=e1,
        titulo="Sistema de Seguimiento Académico",
        defaults={
            "descripcion": "Proyecto demo para validar CRUD, estados y comentarios.",
            "estado": Proyecto.Estado.ENVIADO,
        },
    )
    p2, _ = Proyecto.objects.get_or_create(
        estudiante=e1,
        titulo="Análisis de Datos para Educación",
        defaults={
            "descripcion": "Proyecto demo: en revisión con calificación parcial.",
            "estado": Proyecto.Estado.REVISION,
            "fecha_revision": timezone.now(),
            "calificacion": 4.2,
        },
    )
    p3, _ = Proyecto.objects.get_or_create(
        estudiante=e2,
        titulo="Aplicación Web de Tutorías",
        defaults={
            "descripcion": "Proyecto demo: aprobado (comentarios bloqueados).",
            "estado": Proyecto.Estado.APROBADO,
            "fecha_revision": timezone.now(),
            "calificacion": 4.8,
        },
    )

    _ensure_comment(p1, d1, "Recibido. En breve reviso el documento y te comento observaciones.")
    _ensure_comment(p2, d1, "Buen avance. Ajusta el alcance del dataset y agrega referencias.")
    _ensure_comment(p2, e1, "Listo profe, hoy subo la actualización con las referencias.")
    _ensure_comment(p3, d1, "Aprobado. Excelente trabajo.")


def _ensure_comment(proyecto: Proyecto, usuario: User, texto: str) -> None:
    # Evita duplicados por texto/usuario/proyecto
    if Comentario.objects.filter(proyecto=proyecto, usuario=usuario, texto=texto).exists():
        return
    Comentario.objects.create(proyecto=proyecto, usuario=usuario, texto=texto)

