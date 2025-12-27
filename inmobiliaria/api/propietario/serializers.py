from rest_framework import serializers
from inmobiliaria.models import Propietario
from inmobiliaria.validators import normalizar_rut, validar_rut, validar_telefono_cl
from inmobiliaria.serializers import *

class PropietarioPerfilSerializer(serializers.ModelSerializer):
    # direcciones completas (por si quieres mostrarlas en el futuro)
    direcciones = PropietarioDireccionSerializer(many=True, read_only=True)

    # campos planos de la dirección principal (para el formulario de perfil)
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
            # OJO: aquí asumo que comuna y región pueden venir por defecto
            # si en tu modelo son obligatorias, luego las ajustamos con IDs
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