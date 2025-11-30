from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from datetime import datetime
from django.utils import timezone

from django.db.models import Sum, Count, Q

from rest_framework import viewsets, status, generics, filters, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from .models import *
from .serializers import (
    RegionSerializer,
    ComunaSerializer,
    PropietarioDireccionSerializer,
    PropietarioSerializer,
    PropiedadSerializer,
    InteresadoSerializer,
    VisitaSerializer,
    PagoSerializer,
    CuotaContratoSerializer,
    PropiedadConFotosSerializer,
    PropiedadFotoSerializer,
    PropiedadDocumentoSerializer,
    NotificacionSerializer,
    UsuarioRegistroSerializer,
    MiniPropiedadSerializer,
    MiniInteresadoSerializer,
    ContratoSerializer,
    ReservaSerializer,
    CustomTokenObtainPairSerializer,
    HistorialSerializer,
    SolicitudClienteSerializer,
    AdminPropietarioSerializer,
    AdminPropiedadSerializer,
)

from .notifications import notificar_usuario

from .config import *
from .utils import *
from .permissions import ReadOnlyOrAdminAsesor

from .permisssions_roles import PropiedadPermission, IsAdmin, IsCliente, IsPropietario, NotificacionPermission

from .filters import PropiedadFilter

# Create your views here.


def index(request):
    return render(request,'index.html')
def hello(request):
    return HttpResponse("Hello World")

def about(request):
    return HttpResponse("About")

def propietario(request):
    propietario = list(Propietario.objects.values())
    return JsonResponse(propietario, safe=False)

def propiedad(request, id):
    propiedades = get_object_or_404(Propiedad, id=id)
    return HttpResponse('propiedad: %s' % propiedades.titulo)



class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all().order_by('nombre_region')
    serializer_class = RegionSerializer
    permission_classes = [ReadOnlyOrAdminAsesor]

class ComunaViewSet(viewsets.ModelViewSet):
    queryset = Comuna.objects.select_related('region').all().order_by('nombre_comuna')
    serializer_class = ComunaSerializer
    permission_classes = [ReadOnlyOrAdminAsesor]

class PropietarioViewSet(viewsets.ModelViewSet):
    queryset = Propietario.objects.all().order_by('primer_nombre')
    serializer_class = PropietarioSerializer
    permission_classes = [ReadOnlyOrAdminAsesor]

class PropietarioDireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion_propietario.objects.select_related('propietario','comuna','region').all().order_by('principal','-fecha')
    serializer_class = PropietarioDireccionSerializer
    permission_classes = [ReadOnlyOrAdminAsesor]

class InteresadoViewSet(viewsets.ModelViewSet):
    queryset = Interesado.objects.all().order_by('-id')
    serializer_class = InteresadoSerializer
    permission_classes = [ReadOnlyOrAdminAsesor]

class PropiedadDocumentoViewSet(viewsets.ModelViewSet):
    queryset = PropiedadDocumento.objects.all().order_by("-subido")
    serializer_class = PropiedadDocumentoSerializer
    permission_classes = [ReadOnlyOrAdminAsesor]


class VisitaViewSet(viewsets.ModelViewSet):
    queryset = Visita.objects.all().order_by("-id")
    serializer_class = VisitaSerializer
    permission_classes = [ReadOnlyOrAdminAsesor]

    @action(detail=False, methods=["GET"], url_path="slots")
    def slots(self, request):
        prop_id = request.query_params.get("propiedad")
        fecha_str = request.query_params.get("fecha")
        if not prop_id or not fecha_str:
            return Response({"detail": "Falta propiedad o fecha"}, status=400)
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Formato de fecha inválido (YYYY-MM-DD)"}, status=400)

        libres = slots_disponibles_para_propiedad(int(prop_id), fecha)
        return Response([h.strftime("%H:%M") for h in libres], status=200)

    @action(detail=False, methods=["GET"], url_path="agenda")
    def agenda(self, request):
        prop_id = request.query_params.get("propiedad")
        if not prop_id:
            return Response({"detail": "Falta propiedad"}, status=400)

        start_str = request.query_params.get("start")
        days_str = request.query_params.get("days")

        start = None
        if start_str:
            try:
                start = datetime.strptime(start_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"detail": "start inválido, use YYYY-MM-DD"}, status=400)

        days = DEFAULT_DAYS_PAGE
        if days_str:
            try:
                days = int(days_str)
            except ValueError:
                pass
        if days < 1:
            days = 1
        if days > MAX_DAYS_PAGE:
            days = MAX_DAYS_PAGE

        data = generar_agenda_disponible(int(prop_id), start_date=start, days=days)
        return Response(data, status=200)



class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        base = (
            Reserva.objects
            .select_related("interesado", "propiedad")
            .all()
            .order_by("-fecha")
        )

        if rol == "ADMIN":
            return base
        if rol == "CLIENTE":
            return base.filter(interesado__usuario=user)
        if rol == "PROPIETARIO":
            return base.filter(propiedad__propietario_user=user)
        return base.none()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        user = request.user
        propiedad = reserva.propiedad

        es_propietario = False
        if hasattr(propiedad, "propietario_user") and propiedad.propietario_user == user:
            es_propietario = True
        elif hasattr(propiedad, "propietario") and getattr(propiedad.propietario, "usuario_id", None) == user.id:
            es_propietario = True

        if not es_propietario:
            return Response(
                {"detail": "No tienes permiso para cancelar esta reserva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not reserva.activa:
            return Response(
                {"detail": "La reserva ya está cancelada o cerrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reserva.expires_at and reserva.expires_at < timezone.now():
            return Response(
                {"detail": "No puedes cancelar una reserva vencida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- Cancelar ----
        reserva.activa = False
        reserva.estado_reserva = "cancelada"
        reserva.save()

        # ---- Notificaciones ----
        interesado = reserva.interesado

        propietario_user = getattr(propiedad, "propietario_user", None)
        if not propietario_user and hasattr(propiedad, "propietario"):
            propietario_user = getattr(propiedad.propietario, "usuario", None)

        cliente_user = getattr(interesado, "usuario", None)

        titulo = f"Reserva cancelada en '{propiedad.titulo}'"

        msg_prop = (
            f"Has cancelado la reserva #{reserva.id} de "
            f"{interesado.nombre_completo} para la propiedad '{propiedad.titulo}'."
        )
        notificar_usuario(propietario_user, titulo, msg_prop, tipo="RESERVA")

        if cliente_user:
            msg_cli = (
                f"El propietario ha cancelado tu reserva #{reserva.id} "
                f"para la propiedad '{propiedad.titulo}'."
            )
            notificar_usuario(cliente_user, titulo, msg_cli, tipo="RESERVA")

        serializer = self.get_serializer(reserva)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def perform_create(self, serializer):
        reserva = serializer.save(creada_por=self.request.user)
        prop = reserva.propiedad
        interesado = reserva.interesado

        propietario_user = getattr(prop, "propietario_user", None)
        if not propietario_user and hasattr(prop, "propietario"):
            propietario_user = getattr(prop.propietario, "usuario", None)

        # cliente 
        cliente_user = getattr(interesado, "usuario", None)

        titulo = f"Nueva reserva en '{prop.titulo}'"

        msg_prop = (
            f"Se creó la reserva #{reserva.id} para la propiedad '{prop.titulo}' "
            f"a nombre de {interesado.nombre_completo} por "
            f"${reserva.monto_reserva:,.0f}."
        )
        notificar_usuario(propietario_user, titulo, msg_prop, tipo="RESERVA")

        if cliente_user:
            msg_cli = (
                f"Hemos registrado tu reserva #{reserva.id} para la propiedad "
                f"'{prop.titulo}' por ${reserva.monto_reserva:,.0f}."
            )
            notificar_usuario(cliente_user, titulo, msg_cli, tipo="RESERVA")
    
    
class ContratoViewSet(viewsets.ModelViewSet):
    serializer_class = ContratoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        qs = Contrato.objects.all().select_related("comprador_arrendatario", "propiedad").order_by("-fecha_firma")
        if rol == "ADMIN":
            return qs
        if rol == "CLIENTE":
            return qs.filter(comprador_arrendatario__usuario=user)
        if rol == "PROPIETARIO":
            return qs.filter(propiedad__propietario_user=user)
        return qs.none()

    def get_permissions(self):
        # Solo ADMIN puede crear/editar/eliminar contratos
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return super().get_permissions()

class PagoViewSet(viewsets.ModelViewSet):
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        qs = (
            Pago.objects
            .select_related("contrato", "contrato__comprador_arrendatario", "contrato__propiedad")
            .all()
            .order_by("-fecha")
        )
        if rol == "ADMIN":
            return qs
        if rol == "CLIENTE":
            return qs.filter(contrato__comprador_arrendatario__usuario=user)
        if rol == "PROPIETARIO":
            return qs.filter(contrato__propiedad__propietario_user=user)
        return qs.none()

    def perform_create(self, serializer):
        pago = serializer.save()
        contrato = pago.contrato
        prop = contrato.propiedad
        comprador = contrato.comprador_arrendatario

        propietario_user = getattr(prop, "propietario_user", None)
        if not propietario_user and hasattr(prop, "propietario"):
            propietario_user = getattr(prop.propietario, "usuario", None)

        cliente_user = getattr(comprador, "usuario", None)

        titulo = f"Pago registrado para '{prop.titulo}'"

        msg_prop = (
            f"Se registró un pago de ${pago.monto:,.0f} para el contrato "
            f"#{contrato.id} de la propiedad '{prop.titulo}'."
        )
        notificar_usuario(propietario_user, titulo, msg_prop, tipo="PAGO")

        if cliente_user:
            msg_cli = (
                f"Hemos registrado tu pago de ${pago.monto:,.0f} "
                f"para el contrato #{contrato.id} de la propiedad '{prop.titulo}'."
            )
            notificar_usuario(cliente_user, titulo, msg_cli, tipo="PAGO")

    
class PropiedadViewSet(viewsets.ModelViewSet):
    queryset = Propiedad.objects.all().order_by("-fecha_registro")
    permission_classes = [PropiedadPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropiedadFilter
    search_fields = ["titulo", "descripcion", "ciudad", "propietario__primer_nombre", "propietario__rut"]
    ordering_fields = ["precio", "metros2", "dormitorios", "banos", "fecha_registro"]
    ordering = ["-fecha_registro"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return PropiedadConFotosSerializer
        return PropiedadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # visitante no autenticado
        if not user.is_authenticated:
            return qs.filter(aprobada=True)

        rol = getattr(user, "rol", "")

        # admin ve todo
        if rol == "ADMIN":
            return qs

        if rol == "PROPIETARIO":
            return qs.filter(
                Q(aprobada=True) | Q(propietario_user=user)
            )

        return qs.filter(aprobada=True)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        if user and getattr(user, "rol", "") == "PROPIETARIO":
            # Propiedad creada por propietario: queda pendiente, no aprobada
            serializer.save(
                propietario_user=user,
                aprobada=False,
                estado_aprobacion="pendiente",
            )
        else:
            serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def aprobar(self, request, pk=None):
        propiedad = self.get_object()
        propiedad.aprobada = True
        propiedad.estado_aprobacion = "aprobada"
        propiedad.observacion_admin = ""
        propiedad.save(update_fields=["aprobada", "estado_aprobacion", "observacion_admin"])
        return Response({"detail": "Propiedad aprobada exitosamente."})

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def rechazar(self, request, pk=None):
        propiedad = self.get_object()
        obs = request.data.get("observacion", "")
        propiedad.aprobada = False
        propiedad.estado_aprobacion = "rechazada"
        propiedad.observacion_admin = obs
        propiedad.save(update_fields=["aprobada", "estado_aprobacion", "observacion_admin"])
        return Response({"detail": "Propiedad rechazada.", "observacion": obs})

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def pausar(self, request, pk=None):
        propiedad = self.get_object()
        propiedad.aprobada = False
        propiedad.estado_aprobacion = "pausada"
        propiedad.save(update_fields=["aprobada", "estado_aprobacion"])
        return Response({"detail": "Propiedad pausada."})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        user = request.user
        rol = getattr(user, "rol", "")

        if rol == "PROPIETARIO" and instance.propietario_user_id != user.id:
            raise PermissionDenied("No puedes modificar propiedades que no son tuyas.")

        data = request.data.copy()

        if rol == "PROPIETARIO" and instance.aprobada:
            campos_permitidos = {"descripcion", "precio"}
            keys_to_remove = [k for k in data.keys() if k not in campos_permitidos]
            for k in keys_to_remove:
                data.pop(k, None)
            if not data:
                raise PermissionDenied(
                    "No tienes permiso para modificar otros campos de una propiedad aprobada."
                )

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
    
    @action(detail=True, methods=["get"], url_path="historial")
    def historial(self, request, pk=None):
        propiedad = self.get_object()
        qs = Historial.objects.filter(propiedad=propiedad).order_by("-fecha")
        serializer = HistorialSerializer(qs, many=True)
        return Response(serializer.data)


class PropiedadFotoViewSet(viewsets.ModelViewSet):
    queryset = PropiedadFoto.objects.select_related("propiedad").all()
    serializer_class = PropiedadFotoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["propiedad"]  # permite ?propiedad=1

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        rol = getattr(user, "rol", "")
        if rol == "ADMIN":
            return qs
        if rol == "PROPIETARIO":
            return qs.filter(propiedad__propietario_user=user)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        rol = getattr(user, "rol", "")

        prop = serializer.validated_data.get("propiedad")
        if rol == "PROPIETARIO":
            if not prop or prop.propietario_user_id != user.id:
                raise PermissionDenied(
                    "No puedes subir fotos para propiedades que no son tuyas."
                )
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        rol = getattr(user, "rol", "")

        if rol == "PROPIETARIO" and instance.propiedad.propietario_user_id != user.id:
            raise PermissionDenied("No puedes eliminar fotos de otras propiedades.")

        super().perform_destroy(instance)

    @action(detail=True, methods=["post"])
    def marcar_principal(self, request, pk=None):
        foto = self.get_object()
        user = request.user
        rol = getattr(user, "rol", "")

        if rol == "PROPIETARIO" and foto.propiedad.propietario_user_id != user.id:
            raise PermissionDenied(
                "No puedes modificar fotos de una propiedad que no es tuya."
            )

        foto.principal = True
        foto.save(update_fields=["principal"])
        return Response({"detalle": "Foto marcada como principal."}, status=200)

    
class CuotaContratoViewSet(viewsets.ModelViewSet):
    queryset = CuotaContrato.objects.select_related("contrato", "pago").all()
    serializer_class = CuotaContratoSerializer 

    @action(detail=True, methods=["post"])
    def pagar(self, request, pk=None):
        cuota = self.get_object()
        ser = PagarCuotaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        pago = cuota.registrar_pago(**ser.validated_data)
        return Response({"detalle": "Cuota pagada correctamente.", "pago_id": pago.id}, status=status.HTTP_200_OK)
    
class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated, NotificacionPermission]
    filterset_fields = ["tipo", "leida"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Notificacion.objects.select_related("usuario").order_by("-created_at")
        user = self.request.user
        if getattr(user, "rol", "") == "ADMIN":
            return qs
        return qs.filter(usuario=user)

    @action(detail=True, methods=["post"])
    def leer(self, request, pk=None):
        notif = self.get_object()
        notif.leida = True
        notif.save(update_fields=["leida"])
        return Response({"detalle": "Notificación marcada como leída."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="marcar-todas")
    def marcar_todas(self, request):
        user = request.user
        qs = self.get_queryset().filter(leida=False)
        updated = qs.update(leida=True)
        return Response({"detalle": f"{updated} notificaciones marcadas como leídas."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="contador")
    def contador(self, request):
        qs = self.get_queryset()
        total = qs.count()
        no_leidas = qs.filter(leida=False).count()
        por_tipo = (
            qs.values("tipo")
              .annotate(total=Count("id"), no_leidas=Count("id", filter=models.Q(leida=False)))
        )
        return Response({
            "total": total,
            "no_leidas": no_leidas,
            "por_tipo": {row["tipo"]: {"total": row["total"], "no_leidas": row["no_leidas"]} for row in por_tipo}
        }, status=status.HTTP_200_OK)


class SolicitudClienteViewSet(viewsets.ModelViewSet):
    serializer_class = SolicitudClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        qs = SolicitudCliente.objects.select_related("interesado").order_by("-created_at")

        if rol == "ADMIN":
            return qs
        if rol == "CLIENTE":
            return qs.filter(interesado__usuario=user)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        interesado = Interesado.objects.filter(usuario=user).first()
        if not interesado:
            raise ValidationError("No se encontró un perfil de interesado asociado a tu usuario.")
        serializer.save(interesado=interesado)

class MisContratosView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContratoSerializer
    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        if rol == "ADMIN":
            return Contrato.objects.all().select_related("comprador_arrendatario", "propiedad")
        if rol == "CLIENTE":
            return Contrato.objects.filter(
                comprador_arrendatario__usuario=user
            ).select_related("comprador_arrendatario", "propiedad")
        if rol == "PROPIETARIO":
            return Contrato.objects.filter(
                propiedad__propietario_user=user
            ).select_related("comprador_arrendatario", "propiedad")
        return Contrato.objects.none()

class MisPagosView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PagoSerializer
    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        if rol == "ADMIN":
            return Pago.objects.all().select_related("contrato", "contrato__comprador_arrendatario", "contrato__propiedad")
        if rol == "CLIENTE":
            return Pago.objects.filter(
                contrato__comprador_arrendatario__usuario=user
            ).select_related("contrato", "contrato__comprador_arrendatario", "contrato__propiedad")
        if rol == "PROPIETARIO":
            return Pago.objects.filter(
                contrato__propiedad__propietario_user=user
            ).select_related("contrato", "contrato__comprador_arrendatario", "contrato__propiedad")
        return Pago.objects.none()

class MisReservasView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservaSerializer
    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        if rol == "ADMIN":
            return Reserva.objects.all().select_related("interesado", "propiedad")
        if rol == "CLIENTE":
            return Reserva.objects.filter(
                interesado__usuario=user
            ).select_related("interesado", "propiedad")
        if rol == "PROPIETARIO":
            return Reserva.objects.filter(
                propiedad__propietario_user=user
            ).select_related("interesado", "propiedad")
        return Reserva.objects.none()
    
class CatalogoPropiedadesView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PropiedadConFotosSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # filtros básicos
    filterset_fields = {
        "ciudad": ["exact", "icontains"],
        "tipo": ["exact"],
        "dormitorios": ["gte", "lte"],
        "baos": ["gte", "lte"],     
        "precio": ["gte", "lte"],
    }
    search_fields = ["titulo", "descripcion", "ciudad"]
    ordering_fields = ["precio", "metros2", "dormitorios", "baos", "fecha_registro"]
    ordering = ["-fecha_registro"]

    def get_queryset(self):
        return Propiedad.objects.filter(aprobada=True).order_by("-fecha_registro")


class MisPropiedadesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PropiedadConFotosSerializer

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        if rol == "PROPIETARIO":
            return Propiedad.objects.filter(
                propietario_user=user
            ).order_by("-fecha_registro")

        if rol == "ADMIN":
            return Propiedad.objects.all().order_by("-fecha_registro")

        # Cliente no debería ver "mis propiedades"
        return Propiedad.objects.none()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        nombre = (request.data.get('nombre') or '').strip()
        email = (request.data.get('email') or '').strip()
        password = request.data.get('password') or ''

        if not email or not password:
            return Response(
                {'detail': 'Email y contraseña son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = email.lower()   # podemos usar el correo como username

        if user.objects.filter(username=username).exists():
            return Response(
                {'detail': 'Ya existe un usuario con ese correo.'},
                status=status.HTTP_400_BAD_REQUEST
            )


        user = user.objects.create_user(
            username=username,
            email=email,
            password=password,
        )


        if hasattr(user, "first_name"):
            user.first_name = nombre
            user.save()

        return Response(
            {'detail': 'Usuario creado correctamente.'},
            status=status.HTTP_201_CREATED
        )
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class MiPerfilPropietarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = (request.user.email or "").lower()
        if not email:
            return Response(
                {"detail": "Tu usuario no tiene email asociado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        propietario = Propietario.objects.filter(email__iexact=email).first()
        if not propietario:
            return Response(
                {"detail": "No se encontró un propietario asociado a tu cuenta."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = PropietarioSerializer(propietario).data
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        email = (request.user.email or "").lower()
        propietario = Propietario.objects.filter(email__iexact=email).first()
        if not propietario:
            return Response(
                {"detail": "No se encontró un propietario asociado a tu cuenta."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PropietarioSerializer(propietario, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MiPerfilClienteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        interesado = Interesado.objects.filter(usuario=user).first()
        if not interesado:
            return Response(
                {"detail": "No se encontró un perfil de cliente asociado a tu cuenta."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = InteresadoSerializer(interesado).data
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        interesado = Interesado.objects.filter(usuario=user).first()
        if not interesado:
            return Response(
                {"detail": "No se encontró un perfil de cliente asociado a tu cuenta."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InteresadoSerializer(interesado, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_resumen(request):
    ahora = timezone.now()
    hoy = ahora.date()
    inicio_mes = hoy.replace(day=1)

    propiedades_pendientes = Propiedad.objects.filter(
        estado_aprobacion="pendiente"
    ).count()

    reservas_activas = Reserva.objects.filter(
        activa=True,
        expires_at__gt=ahora,
    ).count()

    reservas_vencidas = Reserva.objects.filter(
        activa=True,
        expires_at__lte=ahora,
    ).count()

    solicitudes_nuevas = SolicitudCliente.objects.filter(
        estado="nueva"
    ).count()

    contratos_vigentes = Contrato.objects.filter(
        vigente=True
    ).count()

    pagos_mes_qs = Pago.objects.filter(fecha__gte=inicio_mes)
    pagos_mes_agg = pagos_mes_qs.aggregate(
        total=Sum("monto"),
        cantidad=Count("id"),
    )
    pagos_mes_monto = pagos_mes_agg["total"] or 0
    pagos_mes_count = pagos_mes_agg["cantidad"] or 0

    notificaciones_no_leidas = Notificacion.objects.filter(
        leida=False
    ).count()

    data = {
        "propiedades_pendientes": propiedades_pendientes,
        "reservas_activas": reservas_activas,
        "reservas_vencidas": reservas_vencidas,
        "solicitudes_nuevas": solicitudes_nuevas,
        "contratos_vigentes": contratos_vigentes,
        "pagos_mes_monto": pagos_mes_monto,
        "pagos_mes_count": pagos_mes_count,
        "notificaciones_no_leidas": notificaciones_no_leidas,
    }
    return Response(data, status=status.HTTP_200_OK)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        es_admin = getattr(user, "rol", "") == "ADMIN" or user.is_staff
        if request.method in permissions.SAFE_METHODS:
            return es_admin
        return es_admin
