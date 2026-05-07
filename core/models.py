from django.conf import settings
from django.db import models


class Proyecto(models.Model):
    class Estado(models.TextChoices):
        ENVIADO = "enviado", "Enviado"
        REVISION = "revision", "En Revisión"
        APROBADO = "aprobado", "Aprobado"

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="proyectos",
        on_delete=models.CASCADE,
    )
    documento = models.FileField(upload_to="proyectos/", null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ENVIADO,
    )
    fecha_envio = models.DateTimeField(auto_now_add=True)
    fecha_revision = models.DateTimeField(null=True, blank=True)
    calificacion = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-fecha_envio"]

    @property
    def comentarios_bloqueados(self) -> bool:
        return self.estado == self.Estado.APROBADO

    def __str__(self) -> str:
        return self.titulo


class Comentario(models.Model):
    proyecto = models.ForeignKey(Proyecto, related_name="comentarios", on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    texto = models.TextField()

    class Meta:
        ordering = ["-fecha"]

    def __str__(self) -> str:
        return f"Comentario({self.proyecto_id}) por {self.usuario_id}"
