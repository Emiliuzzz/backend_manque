from django.contrib.auth import get_user_model

from rest_framework import generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.views import TokenObtainPairView

from inmobiliaria.models import Propiedad, Contrato, Pago, Reserva
from inmobiliaria.serializers import (
    PropiedadConFotosSerializer,
    ContratoSerializer,
    PagoSerializer,
    ReservaSerializer,
    CustomTokenObtainPairSerializer,
    CambiarPasswordSerializer,
)


User = get_user_model()
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        nombre = request.data.get("nombre_completo") or request.data.get("nombre")
        email = request.data.get("email")
        password = request.data.get("password")

        if not nombre or not email or not password:
            return Response(
                {"detail": "Faltan datos (nombre, email o contraseña)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = email  


        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "Ya existe un usuario con ese email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=nombre,
        )

        return Response(
            {"detail": "Usuario creado correctamente."},
            status=status.HTTP_201_CREATED,
        )

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



# Catálogo propiedades
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


# Mixtas
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
    



User = get_user_model()

class CambiarPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        password_actual = serializer.validated_data["password_actual"]
        password_nueva = serializer.validated_data["password_nueva"]

        if not user.check_password(password_actual):
            return Response(
                {"detail": "La contraseña actual es incorrecta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password_nueva)
        user.save()

        return Response(
            {"detail": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )