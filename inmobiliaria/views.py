from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from datetime import datetime
from django.utils import timezone

from django.db.models import Q, Count

from rest_framework import viewsets, status, generics, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import get_user_model

from .models import *
from .serializers import *
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
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, "rol", "")
        base = Reserva.objects.select_related("interesado", "propiedad").all().order_by("-fecha")
        if rol == "ADMIN":
            return base
        if rol == "CLIENTE":
            return base.filter(interesado__usuario=user)
        if rol == "PROPIETARIO":
            return base.filter(propiedad__propietario_user=user)
        return base.none()

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
        qs = Pago.objects.select_related("contrato", "contrato__comprador_arrendatario", "contrato__propiedad").all().order_by("-fecha")
        if rol == "ADMIN":
            return qs
        if rol == "CLIENTE":
            return qs.filter(contrato__comprador_arrendatario__usuario=user)
        if rol == "PROPIETARIO":
            return qs.filter(contrato__propiedad__propietario_user=user)
        return qs.none()

    
class PropiedadViewSet(viewsets.ModelViewSet):
    queryset = Propiedad.objects.all().order_by("-fecha_registro")
    permission_classes = [PropiedadPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropiedadFilter
    search_fields = ["titulo", "descripcion", "ciudad", "propietario__primer_nombre", "propietario__rut"]
    ordering_fields = ["precio", "metros2", "dormitorios", "baños", "fecha_registro"]
    ordering = ["-fecha_registro"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return PropiedadConFotosSerializer
        return PropiedadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.filter(aprobada=True)
        rol = getattr(user, "rol", "")
        if rol == "ADMIN":
            return qs
        if rol == "PROPIETARIO":
            return qs.filter(Q(aprobada=True) | Q(propietario_user_id=user.id))
        return qs.filter(aprobada=True)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        if user and getattr(user, "rol", "") == "PROPIETARIO":
            serializer.save(propietario_user=user, aprobada=False)
        else:
            serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def aprobar(self, request, pk=None):
        prop = self.get_object()
        prop.aprobada = True
        prop.save(update_fields=["aprobada"])
        return Response({"detalle": "Propiedad aprobada."}, status=status.HTTP_200_OK)
    
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

Usuario = get_user_model()

class RegistroUsuarioView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioRegistroSerializer
    permission_classes = [AllowAny]


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
        "baños": ["gte", "lte"],
        "precio": ["gte", "lte"],
    }
    search_fields = ["titulo", "descripcion", "ciudad"]
    ordering_fields = ["precio", "metros2", "dormitorios", "baños", "fecha_registro"]
    ordering = ["-fecha_registro"]

    def get_queryset(self):
        return Propiedad.objects.filter(aprobada=True).order_by("-fecha_registro")