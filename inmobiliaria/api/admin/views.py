from django.db.models import Sum, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser

from inmobiliaria.models import Propietario, Propiedad, SolicitudCliente, Reserva, Pago
from inmobiliaria.permisssions_roles import IsAdmin

from .serializers import *
from inmobiliaria.serializers import SolicitudClienteSerializer


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


# CRUD
User = get_user_model()

@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def admin_usuarios_list(request):
    if request.method == "GET":
        rol = (request.GET.get("rol") or "TODOS").strip().upper()
        search = (request.GET.get("search") or "").strip()

        qs = User.objects.all().order_by("-id")

        if rol != "TODOS":
            qs = qs.filter(rol=rol)

        if search:
            search_l = search.lower()

            emails_perfiles = set(
                Propietario.objects.filter(
                    Q(email__icontains=search_l)
                    | Q(rut__icontains=search_l)
                    | Q(primer_nombre__icontains=search_l)
                    | Q(primer_apellido__icontains=search_l)
                    | Q(segundo_nombre__icontains=search_l)
                    | Q(segundo_apellido__icontains=search_l)
                ).values_list("email", flat=True)
            )

            emails_perfiles |= set(
                Interesado.objects.filter(
                    Q(email__icontains=search_l)
                    | Q(rut__icontains=search_l)
                    | Q(primer_nombre__icontains=search_l)
                    | Q(primer_apellido__icontains=search_l)
                    | Q(segundo_nombre__icontains=search_l)
                    | Q(segundo_apellido__icontains=search_l)
                ).values_list("email", flat=True)
            )

            emails_perfiles = [e.strip().lower() for e in emails_perfiles if e]

            qs = qs.filter(
                Q(email__icontains=search_l)
                | Q(username__icontains=search_l)
                | Q(email__in=emails_perfiles)
            )

        return Response(AdminUsuarioSerializer(qs, many=True).data)

    # ---- POST: crear usuario + perfil ----
    ser = AdminUsuarioCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.save()
    return Response(
        AdminUsuarioSerializer(user).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT"])
@permission_classes([IsAdminUser])
def admin_usuario_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "No encontrado"}, status=404)

    if request.method == "GET":
        return Response(AdminUsuarioSerializer(user).data)

    old_email = (user.email or "").strip().lower()

    ser = AdminUsuarioUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    if "email" in data:
        user.email = data["email"].strip().lower()
        user.username = data["email"].strip().lower()

    if "rol" in data:
        user.rol = data["rol"]

    if "is_active" in data:
        user.is_active = data["is_active"]

    if "aprobado" in data:
        user.aprobado = data["aprobado"]

    user.save()

    new_email = (user.email or "").strip().lower()

    if user.rol == "PROPIETARIO":
        p = Propietario.objects.filter(email__iexact=old_email).first() or Propietario.objects.filter(email__iexact=new_email).first()
        if p:
            if old_email != new_email:
                p.email = new_email
            for f in ["primer_nombre", "segundo_nombre", "primer_apellido", "segundo_apellido", "telefono"]:
                if f in data:
                    setattr(p, f, data[f])
            p.save()

    if user.rol == "CLIENTE":
        c = Interesado.objects.filter(email__iexact=old_email).first() or Interesado.objects.filter(email__iexact=new_email).first()
        if c:
            if old_email != new_email:
                c.email = new_email
            for f in ["primer_nombre", "segundo_nombre", "primer_apellido", "segundo_apellido", "telefono"]:
                if f in data:
                    setattr(c, f, data[f])
            c.save()

    return Response(AdminUsuarioSerializer(user).data)



@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_usuario_crear_perfil(request, pk: int):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)

    ser = AdminUsuarioCrearPerfilSerializer(data=request.data, context={"user": user})
    ser.is_valid(raise_exception=True)
    ser.save()

    # devolver el usuario actualizado con su perfil ya asociado
    user.refresh_from_db()
    return Response(AdminUsuarioSerializer(user).data, status=status.HTTP_201_CREATED)



@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_usuario_desactivar(request, pk: int):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)

    user.is_active = False
    user.save(update_fields=["is_active"])
    return Response({"ok": True})



@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_usuario_activar(request, pk: int):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)

    user.is_active = True
    user.save(update_fields=["is_active"])
    return Response({"ok": True})


