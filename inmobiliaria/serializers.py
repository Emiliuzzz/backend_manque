from rest_framework import serializers
from .models import *
from .validators import *
from .config import *
from .utils import slots_futuro
from django.utils import timezone

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'nombre_region']

class ComunaSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    id_region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), source='region', write_only=True
    )

    class Meta:
        model = Comuna
        fields = ['id', 'nombre_comuna', 'region', 'id_region']

class PropietarioDireccionSerializer(serializers.ModelSerializer):
    comuna = ComunaSerializer(read_only=True)
    id_comuna = serializers.PrimaryKeyRelatedField(queryset=Comuna.objects.all(), source='comuna', write_only=True)
    region = RegionSerializer(read_only=True)
    id_region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), source='region', write_only=True)

    class Meta:
        model = Direccion_propietario
        fields = [
            'id','calle_o_pasaje','numero','poblacion_o_villa',
            'comuna','id_comuna','region','id_region','referencia','codigo_postal',
            'principal','fecha'
        ]

class PropietarioSerializer(serializers.ModelSerializer):
    direcciones = PropietarioDireccionSerializer(many=True, read_only=True)
    class Meta:
        model = Propietario
        fields = ['id','primer_nombre', "segundo_nombre", "primer_apellido", "segundo_apellido",'rut','telefono','email','direcciones']

    def validar_rut(self, value):
        v = normalizar_rut(value)
        validar_rut(v)
        return v
    
    def validar_telefono(self, value):
        if value:
            validar_telefono_cl(value)
        return value
    
class InteresadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interesado
        fields = "__all__"


class VisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visita
        fields = "__all__"

    def validate(self, attrs):
        fecha = attrs.get("fecha", getattr(self.instance, "fecha", None))
        hora = attrs.get("hora", getattr(self.instance, "hora", None))
        propiedad = attrs.get("propiedad", getattr(self.instance, "propiedad", None))
        interesado = attrs.get("interesado", getattr(self.instance, "interesado", None))

        hoy = timezone.localdate()
        delta = (fecha - hoy).days
        if delta < 0 or delta > VENTANA_FUTURA_MAX_DIAS:
            raise serializers.ValidationError(f"La fecha debe estar entre hoy y {VENTANA_FUTURA_MAX_DIAS} días en el futuro.")
        if fecha.weekday() > 4:
            raise serializers.ValidationError("Las visitas solo se pueden agendar de lunes a viernes.")
        if Feriado.objects.filter(fecha=fecha).exists():
            raise serializers.ValidationError("No se puede agendar en días feriados.")
        if hora not in INTERVALO_PERMITIDOS:
            raise serializers.ValidationError("La hora debe ser un slot válido: 09–13 o 16–18 (en punto).")
        if not slots_futuro(fecha, hora):
            raise serializers.ValidationError("La hora seleccionada ya pasó o está fuera del margen mínimo.")

        dup = Visita.objects.filter(propiedad=propiedad, fecha=fecha, hora=hora)
        if self.instance:
            dup = dup.exclude(pk=self.instance.pk)
        if dup.exists():
            raise serializers.ValidationError("Ese horario ya está reservado para la propiedad.")

        activas = Visita.objects.filter(
            interesado=interesado,
            fecha__gte=hoy,
            estado__in=ESTADOS_ACTIVOS,
        ).exclude(pk=getattr(self.instance, "pk", None)).count()
        if activas >= MAX_VISITAS_ACTIVAS_POR_INTERESADO:
            raise serializers.ValidationError(f"Has alcanzado el límite de {MAX_VISITAS_ACTIVAS_POR_INTERESADO} visitas activas.")

        return attrs