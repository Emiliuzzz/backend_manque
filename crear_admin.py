import os
import sys

print("== Iniciando script crear_admin.py ==")

# Asegúrate de que el módulo de settings es correcto
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
print("DJANGO_SETTINGS_MODULE =", os.environ.get("DJANGO_SETTINGS_MODULE"))

# Muestra si ve DATABASE_URL (debería estar seteado)
print("DATABASE_URL presente?", bool(os.environ.get("DATABASE_URL")))

try:
    import django
    django.setup()
    print("Django cargado OK")
except Exception as e:
    print("ERROR al hacer django.setup():", repr(e))
    sys.exit(1)

from django.contrib.auth import get_user_model
from django.db import connection

# Dato útil para confirmar a qué DB te estás conectando
print("Engine:", connection.vendor)
print("DB settings NAME:", connection.settings_dict.get("NAME"))

User = get_user_model()

username = "admin"
password = "admin123"
email = "admin@example.com"

try:
    if User.objects.filter(username=username).exists():
        print(f"El usuario '{username}' YA existe.")
    else:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superusuario '{username}' creado con ÉXITO.")
except Exception as e:
    print("ERROR creando superusuario:", repr(e))
