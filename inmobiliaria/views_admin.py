from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum

from .models import Propietario, Propiedad, SolicitudCliente, Reserva, Pago
from .serializers import (
    AdminPropietarioSerializer,
    AdminPropiedadSerializer,
    SolicitudClienteSerializer,
)

from .permisssions_roles import IsAdmin
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsAdmin])
def admin_resumen(request):
    hoy = timezone.localdate()

    propiedades_por_aprobar = Propiedad.objects.filter(
        estado_aprobacion__in=["pendiente", "en_revision"]
    ).count()

    reservas_activas = Reserva.objects.filter(
        activa=True,
        expires_at__gt=timezone.now(),
    ).count()

    solicitudes_nuevas = SolicitudCliente.objects.filter(
        estado="nueva"
    ).count()

    pagos_mes = (
        Pago.objects.filter(
            fecha__year=hoy.year,
            fecha__month=hoy.month,
        ).aggregate(total=Sum("monto"))["total"]
        or 0
    )

    data = {
        "total_propiedades": Propiedad.objects.count(),
        "total_propietarios": Propietario.objects.count(),
        "propiedades_por_aprobar": propiedades_por_aprobar,
        "reservas_activas": reservas_activas,
        "solicitudes_nuevas": solicitudes_nuevas,
        "pagos_mes": pagos_mes,
    }
    return Response(data)

# PROPIETARIO
class AdminPropietarioListCreateView(generics.ListCreateAPIView):
    queryset = Propietario.objects.all().order_by('primer_apellido', 'primer_nombre')
    serializer_class = AdminPropietarioSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
class AdminPropietarioRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Propietario.objects.all().order_by('primer_apellido', 'primer_nombre')
    serializer_class = AdminPropietarioSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


# PROPIEDAD
class AdminPropiedadListCreateView(generics.ListCreateAPIView):
    queryset = Propiedad.objects.select_related('propietario').all().order_by('-id')
    serializer_class = AdminPropiedadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class AdminPropiedadRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Propiedad.objects.select_related('propietario').all()
    serializer_class = AdminPropiedadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


# CLIENTE
class AdminSolicitudClienteListView(generics.ListAPIView):
    queryset = SolicitudCliente.objects.select_related("interesado").all().order_by('-created_at')
    serializer_class = SolicitudClienteSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class AdminSolicitudClienteEstadoUpdateView(generics.UpdateAPIView):
    queryset = SolicitudCliente.objects.all()
    serializer_class = SolicitudClienteSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
