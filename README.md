# Academy

Sistema de Seguimiento de Proyectos Académicos (Django).

## Instalación

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo --out demo_users.txt
python manage.py runserver
```

## Rutas

- `/login/`
- `/register/`
- `/proyectos/` (lista + filtros + export CSV/PDF)
