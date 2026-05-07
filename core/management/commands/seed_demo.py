from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand

from core.seed import DEMO_USERS, seed_demo_data


class Command(BaseCommand):
    help = "Crea usuarios/grupos y datos demo para Academy (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            default="demo_users.txt",
            help="Ruta del archivo para guardar credenciales (por defecto: demo_users.txt).",
        )

    def handle(self, *args, **options):
        seed_demo_data()

        out_path = Path(options["out"]).resolve()
        lines = [
            "Academy - Usuarios demo",
            "",
        ]
        for u in DEMO_USERS:
            lines.append(f"- grupo={u.group} | username={u.username} | password={u.password} | email={u.email}")
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        self.stdout.write(self.style.SUCCESS("Seed demo aplicado correctamente."))
        self.stdout.write(self.style.SUCCESS(f"Credenciales guardadas en: {out_path}"))

