from __future__ import annotations

import os
from pathlib import Path
import time
import sqlite3

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
    db_path = Path("/tmp") / "db.sqlite3"

    if sentinel.exists() and _has_auth_tables(db_path):
        return

    lock = Path("/tmp") / ".academy_migrate_lock"

    # Si otra request está migrando, esperamos un poco.
    for _ in range(25):
        if sentinel.exists():
            return
        if not lock.exists():
            break
        time.sleep(0.2)

    # Intenta tomar el lock (best-effort).
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        has_lock = True
    except FileExistsError:
        has_lock = False

    if not has_lock:
        # Espera a que el otro proceso termine
        for _ in range(50):
            if sentinel.exists():
                return
            time.sleep(0.2)
        # Si no apareció sentinel, intentamos migrar igualmente (último recurso)

    try:
        # Asegura que Django esté inicializado antes de call_command
        import django

        django.setup()
        call_command("migrate", interactive=False, run_syncdb=True, verbosity=0)
    except Exception:
        # Si falla, borramos sentinel por si se llegó a crear en paralelo
        if sentinel.exists():
            try:
                sentinel.unlink()
            except Exception:
                pass
        raise
    finally:
        if has_lock:
            try:
                lock.unlink()
            except Exception:
                pass

    # Datos demo opcionales en Vercel
    if os.getenv("ACADEMY_SEED_ON_START", "0") == "1":
        try:
            from core.seed import seed_demo_data

            seed_demo_data()
        except Exception:
            pass

    sentinel.write_text("ok", encoding="utf-8")


def _has_auth_tables(db_path: Path) -> bool:
    """
    Verifica si la DB ya tiene al menos la tabla de auth (indicador de migrate aplicado).
    Si la DB no existe o no se puede abrir, devuelve False.
    """
    try:
        if not db_path.exists():
            return False
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auth_user'")
            return cur.fetchone() is not None
        finally:
            conn.close()
    except Exception:
        return False

