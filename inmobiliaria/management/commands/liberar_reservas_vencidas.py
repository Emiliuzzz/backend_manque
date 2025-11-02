from django.core.management.base import BaseCommand
from django.utils import timezone
from inmobiliaria.models import Reserva, Contrato, Notificacion

def _notificar(usuario, titulo, mensaje, tipo="SISTEMA"):
    if usuario:
        Notificacion.objects.create(usuario=usuario, titulo=titulo[:120], mensaje=mensaje, tipo=tipo)

class Command(BaseCommand):
    help = "Libera propiedades con reservas vencidas"

    def handle(self, *args, **kwargs):
        ahora = timezone.now()
        vencidas = Reserva.objects.filter(activa=True, expires_at__lt=ahora)

        count = 0
        for r in vencidas:
            r.activa = False
            r.save(update_fields=["activa"])

            tiene_otra = Reserva.objects.filter(propiedad=r.propiedad, activa=True).exists()
            contrato_vigente = Contrato.objects.filter(propiedad=r.propiedad, vigente=True).exists()
            if not tiene_otra and not contrato_vigente:
                r.propiedad.estado = "disponible"
                r.propiedad.save(update_fields=["estado"])

            # Notificar propietario y cliente
            propietario_user = getattr(r.propiedad, "propietario_user", None)
            cliente_user = getattr(r.interesado, "usuario", None)
            _notificar(propietario_user, "Reserva vencida", f"La reserva de '{r.propiedad.titulo}' venció y fue liberada.", tipo="RESERVA")
            _notificar(cliente_user, "Tu reserva venció", f"Venció la reserva de '{r.propiedad.titulo}'.", tipo="RESERVA")

            count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} reservas vencidas liberadas."))