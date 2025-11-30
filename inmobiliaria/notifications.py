from django.contrib.auth import get_user_model
from .models import Notificacion

User = get_user_model()

def notificar_usuario(usuario, titulo, mensaje, tipo="SISTEMA"):
    if not usuario:
        return None
    return Notificacion.objects.create(
        usuario=usuario,
        titulo=titulo,
        mensaje=mensaje,
        tipo=tipo,
    )

def notificar_admins(titulo, mensaje, tipo="SISTEMA"):
    admins = User.objects.filter(rol="ADMIN", is_active=True)
    for u in admins:
        Notificacion.objects.create(
            usuario=u,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
        )
