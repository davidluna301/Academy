from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Seed opcional para demo (idempotente). Evita romper si aún no hay migraciones.
        from django.conf import settings

        if not getattr(settings, "ACADEMY_SEED_ON_START", False):
            return

        try:
            from .seed import seed_demo_data

            seed_demo_data()
        except Exception:
            # En arranque (antes de migrar) puede fallar; no bloqueamos el servidor.
            return
