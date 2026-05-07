from __future__ import annotations

import os
from pathlib import Path

from django.core.management import call_command


def ensure_db_ready() -> None:
    """
    En Vercel, SQLite vive en /tmp (efímero). Inicializamos migraciones
    una sola vez por cold start usando un sentinel en /tmp.
    """
    is_vercel = os.getenv("VERCEL") == "1" or bool(os.getenv("VERCEL_URL"))
    if not is_vercel:
        return

    sentinel = Path("/tmp") / ".academy_migrated"
    if sentinel.exists():
        return

    call_command("migrate", interactive=False, run_syncdb=True, verbosity=0)

    # Datos demo opcionales en Vercel
    if os.getenv("ACADEMY_SEED_ON_START", "0") == "1":
        try:
            from core.seed import seed_demo_data

            seed_demo_data()
        except Exception:
            pass

    sentinel.write_text("ok", encoding="utf-8")

