from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    Propiedad, Reserva, Contrato, Pago, Notificacion, Interesado
)

User = get_user_model()

# --------- Helper ---------
def _notificar(usuario, titulo, mensaje, tipo="SISTEMA"):
    """
    Crea una Notificacion si 'usuario' existe.
    """
    if usuario:
        Notificacion.objects.create(
            usuario=usuario,
            titulo=titulo[:120],
            mensaje=mensaje,
            tipo=tipo,
        )

# --------- PROPIEDAD ---------
@receiver(pre_save, sender=Propiedad)
def notificar_aprobacion_propiedad(sender, instance: Propiedad, **kwargs):
    """
    Si una propiedad pasa de no aprobada a aprobada => notificar al propietario_user.
    """
    if not instance.pk:
        return
    try:
        antes = Propiedad.objects.get(pk=instance.pk)
    except Propiedad.DoesNotExist:
        return

    if not antes.aprobada and instance.aprobada:
        titulo = "Tu propiedad fue aprobada"
        mensaje = f"La propiedad '{instance.titulo}' en {instance.ciudad} ha sido aprobada y ahora es pública."
        _notificar(getattr(instance, "propietario_user", None), titulo, mensaje, tipo="SISTEMA")

@receiver(post_save, sender=Propiedad)
def notificar_propiedad_creada(sender, instance: Propiedad, created, **kwargs):
    """
    Si un PROPIETARIO crea una propiedad (aprobada=False por flujo) => notificar a ADMIN (si quieres).
    """
    if not created:
        return
    # Aviso al propietario: recibida
    if instance.propietario_user:
        _notificar(
            instance.propietario_user,
            "Propiedad enviada a revisión",
            f"Tu propiedad '{instance.titulo}' fue recibida y está pendiente de aprobación.",
            tipo="SISTEMA",
        )

    admin = User.objects.filter(is_superuser=True).order_by("id").first()
    if admin:
        _notificar(
            admin,
            "Nueva propiedad pendiente de aprobación",
            f"Se creó '{instance.titulo}' ({instance.ciudad}). Revisa y aprueba si corresponde.",
            tipo="SISTEMA",
        )

# --------- RESERVA ---------
@receiver(post_save, sender=Reserva)
def notificar_reserva_creada(sender, instance: Reserva, created, **kwargs):
    """
    Al crear una reserva: notificar a propietario_user (dueño de la propiedad) y al cliente (interesado.usuario).
    """
    if not created:
        return

    prop = instance.propiedad
    interesado = instance.interesado
    propietario_user = getattr(prop, "propietario_user", None)
    cliente_user = getattr(interesado, "usuario", None)

    titulo_p = "Nueva reserva de tu propiedad"
    msg_p = f"La propiedad '{prop.titulo}' fue reservada por {interesado.nombre_completo}. Vence: {instance.expires_at}."
    _notificar(propietario_user, titulo_p, msg_p, tipo="RESERVA")

    titulo_c = "Reserva creada"
    msg_c = f"Reservaste '{prop.titulo}'. Recuerda que vence el {instance.expires_at}."
    _notificar(cliente_user, titulo_c, msg_c, tipo="RESERVA")

# --------- CONTRATO ---------
@receiver(post_save, sender=Contrato)
def notificar_contrato_creado(sender, instance: Contrato, created, **kwargs):
    """
    Al crear contrato: notificar a cliente y propietario.
    """
    if not created:
        return

    prop = instance.propiedad
    propietario_user = getattr(prop, "propietario_user", None)
    cliente_user = getattr(instance.comprador_arrendatario, "usuario", None)

    t = instance.get_tipo_display()

    _notificar(
        propietario_user,
        f"Contrato de {t} creado",
        f"Se creó un contrato de {t} para '{prop.titulo}' por ${instance.precio_pactado:.0f}.",
        tipo="SISTEMA",
    )
    _notificar(
        cliente_user,
        f"Tu contrato de {t}",
        f"Se registró tu contrato de {t} para '{prop.titulo}'.",
        tipo="SISTEMA",
    )

# --------- PAGO ---------
@receiver(post_save, sender=Pago)
def notificar_pago_creado(sender, instance: Pago, created, **kwargs):
    """
    Al registrar un pago: notificar a cliente y propietario.
    """
    if not created:
        return

    c = instance.contrato
    prop = c.propiedad
    propietario_user = getattr(prop, "propietario_user", None)
    cliente_user = getattr(c.comprador_arrendatario, "usuario", None)

    titulo = "Pago registrado"
    msg_c = f"Se registró un pago de ${instance.monto:.0f} para tu contrato de '{prop.titulo}'."
    msg_p = f"Se registró un pago de ${instance.monto:.0f} en el contrato de '{prop.titulo}'."

    _notificar(cliente_user, titulo, msg_c, tipo="PAGO")
    _notificar(propietario_user, titulo, msg_p, tipo="PAGO")