from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from inmobiliaria.models import Propiedad, Propietario, Reserva, Contrato, Pago
from .serializers import PropietarioPerfilSerializer

from inmobiliaria.serializers import *

class MiPerfilPropietarioView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PropietarioPerfilSerializer

    def get_object(self):
        email = (self.request.user.email or "").lower()
        from rest_framework.exceptions import ValidationError, NotFound

        if not email:
            raise ValidationError("Tu usuario no tiene email asociado.")

        propietario = Propietario.objects.filter(email__iexact=email).first()
        if not propietario:
            raise NotFound("No se encontró un propietario asociado a tu cuenta.")

        return propietario


class MisPropiedadesPropietarioView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PropiedadConFotosSerializer

    def get_queryset(self):
        user = self.request.user
        return Propiedad.objects.filter(propietario_user=user).order_by("-fecha_registro")


class MisReservasPropietarioView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservaSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            Reserva.objects
            .filter(propiedad__propietario_user=user)
            .select_related("interesado", "propiedad")
            .order_by("-fecha")
        )


class MisContratosPropietarioView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContratoSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            Contrato.objects
            .filter(propiedad__propietario_user=user)
            .select_related("comprador_arrendatario", "propiedad")
            .order_by("-fecha_firma")
        )


class MisPagosPropietarioView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PagoSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            Pago.objects
            .filter(contrato__propiedad__propietario_user=user)
            .select_related("contrato", "contrato__comprador_arrendatario", "contrato__propiedad")
            .order_by("-fecha")
        )


class PropietarioPerfilSerializer(serializers.ModelSerializer):
    # direcciones completas 
    direcciones = PropietarioDireccionSerializer(many=True, read_only=True)


    calle = serializers.CharField(required=False, allow_blank=True)
    numero = serializers.CharField(required=False, allow_blank=True)
    poblacion_o_villa = serializers.CharField(required=False, allow_blank=True)
    referencia = serializers.CharField(required=False, allow_blank=True)
    codigo_postal = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Propietario
        fields = [
            "id",
            "primer_nombre", "segundo_nombre",
            "primer_apellido", "segundo_apellido",
            "rut", "telefono", "email",
            # dirección principal
            "calle", "numero", "poblacion_o_villa",
            "referencia", "codigo_postal",
            # opcional
            "direcciones",
        ]
        read_only_fields = ["rut", "email"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        dir_p = instance.direcciones.filter(principal=True).first()

        if dir_p:
            data["calle"] = dir_p.calle_o_pasaje or ""
            data["numero"] = dir_p.numero or ""
            data["poblacion_o_villa"] = dir_p.poblacion_o_villa or ""
            data["referencia"] = dir_p.referencia or ""
            data["codigo_postal"] = dir_p.codigo_postal or ""
        else:
            data["calle"] = ""
            data["numero"] = ""
            data["poblacion_o_villa"] = ""
            data["referencia"] = ""
            data["codigo_postal"] = ""

        return data

    def update(self, instance, validated_data):
        # sacar campos de dirección
        calle = validated_data.pop("calle", None)
        numero = validated_data.pop("numero", None)
        poblacion = validated_data.pop("poblacion_o_villa", None)
        referencia = validated_data.pop("referencia", None)
        codigo_postal = validated_data.pop("codigo_postal", None)

        # actualizar datos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # crear/actualizar dirección principal
        dir_p = instance.direcciones.filter(principal=True).first()
        if not dir_p:
            dir_p = Direccion_propietario(
                propietario=instance,
                calle_o_pasaje=calle or "",
                numero=numero or "",
                poblacion_o_villa=poblacion or "",
                referencia=referencia or "",
                codigo_postal=codigo_postal or "",
                principal=True,
                comuna=instance.direcciones.first().comuna if instance.direcciones.exists() else None,
                region=instance.direcciones.first().region if instance.direcciones.exists() else None,
            )
        else:
            if calle is not None:
                dir_p.calle_o_pasaje = calle
            if numero is not None:
                dir_p.numero = numero
            if poblacion is not None:
                dir_p.poblacion_o_villa = poblacion
            if referencia is not None:
                dir_p.referencia = referencia
            if codigo_postal is not None:
                dir_p.codigo_postal = codigo_postal
            dir_p.principal = True

        dir_p.save()
        return instance