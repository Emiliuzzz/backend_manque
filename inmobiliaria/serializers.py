from rest_framework import serializers
from .models import *
from .validators import *
from .config import *
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from datetime import timedelta
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

    def validate_rut(self, value):
        v = normalizar_rut(value)
        validar_rut(v)
        return v
    
    def validate_telefono(self, value):
        if value:
            validar_telefono_cl(value)
        return value

class PropiedadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propiedad
        fields = "__all__"
        
class InteresadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interesado
        fields = "__all__"

    def validate_rut(self, value):
        v = normalizar_rut(value)
        validar_rut(v)
        return v

    def validate_telefono(self, value):
        if value:
            validar_telefono_cl(value)
        return value



class VisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visita
        fields = "__all__"

    def validate(self, attrs):
        from .utils import slots_futuro
        
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
    


class PagoSerializer(serializers.ModelSerializer):
    contrato_id = serializers.IntegerField(source="contrato.id", read_only=True)
    propiedad = serializers.SerializerMethodField()
    cliente = serializers.SerializerMethodField()

    class Meta:
        model = Pago
        fields = (
            "id",
            "contrato_id",
            "fecha",
            "monto",
            "medio",
            "comprobante",
            "notas",
            "propiedad",
            "cliente",
        )

    def get_propiedad(self, obj):
        p = obj.contrato.propiedad
        return {"id": p.id, "titulo": p.titulo, "ciudad": p.ciudad, "tipo": p.tipo} if p else None

    def get_cliente(self, obj):
        i = obj.contrato.comprador_arrendatario
        return {"id": i.id, "nombre": i.nombre_completo, "rut": i.rut} if i else None

class CuotaContratoSerializer(serializers.ModelSerializer):
    contrato_id = serializers.IntegerField(source="contrato.id", read_only=True)

    class Meta:
        model = CuotaContrato
        fields = ("id", "contrato_id", "vencimiento", "monto", "pagada", "pago")
        read_only_fields = ("pagada", "pago")

class PagarCuotaSerializer(serializers.Serializer):
    monto = serializers.DecimalField(max_digits=12, decimal_places=2)
    fecha = serializers.DateField(required=False)
    medio = serializers.CharField(required=False, default="transferencia")
    notas = serializers.CharField(required=False, allow_blank=True)


class PropiedadConFotosSerializer(serializers.ModelSerializer):
    fotos = serializers.SerializerMethodField()

    class Meta:
        model = Propiedad
        fields = "__all__"

    def get_fotos(self, obj):
        return [
            {
                "id": f.id,
                "url": f.foto.url if f.foto else None,
                "orden": f.orden,
                "principal": f.principal,
            }
            for f in obj.fotos.all().order_by("orden")
        ]


class PropiedadDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropiedadDocumento
        fields = "__all__"

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = "__all__"
        read_only_fields = ["id", "created_at"]

        
Usuario = get_user_model()

class UsuarioRegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ("id", "username", "email", "password", "rol")

    def create(self, validated_data):
        rol = validated_data.get("rol", "CLIENTE")
        user = Usuario(
            username=validated_data["username"],
            email=validated_data.get("email"),
            rol=rol,
        )
        # Si se registra como PROPIETARIO, queda pendiente de aprobación
        if rol == "PROPIETARIO":
            user.aprobado = False
            user.is_active = True 
        user.set_password(validated_data["password"])
        user.save()
        return user
    

class MiniPropiedadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propiedad
        fields = ("id", "titulo", "ciudad", "tipo", "estado", "aprobada")

class MiniInteresadoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)

    class Meta:
        model = Interesado
        fields = ("id", "nombre_completo", "rut", "email", "telefono")

class ContratoSerializer(serializers.ModelSerializer):
    propiedad = MiniPropiedadSerializer(read_only=True)
    comprador_arrendatario = MiniInteresadoSerializer(read_only=True)

    # extras útiles
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    total_pagos = serializers.SerializerMethodField()
    saldo = serializers.SerializerMethodField()

    class Meta:
        model = Contrato
        fields = (
            "id",
            "tipo", "tipo_display",
            "propiedad",
            "comprador_arrendatario",
            "fecha_firma",
            "precio_pactado",
            "vigente",
            "archivo_pdf",
            "total_pagos",
            "saldo",
        )

    def get_total_pagos(self, obj):
        total = obj.pagos.aggregate(total=models.Sum("monto"))["total"]
        return total or 0

    def get_saldo(self, obj):
        total = self.get_total_pagos(obj)
        return (obj.precio_pactado or 0) - total

class ReservaSerializer(serializers.ModelSerializer):
    propiedad = MiniPropiedadSerializer(read_only=True)
    interesado = MiniInteresadoSerializer(read_only=True)

    vencida = serializers.SerializerMethodField()
    estado_reserva = serializers.SerializerMethodField() 

    class Meta:
        model = Reserva
        fields = (
            "id",
            "propiedad",
            "interesado",
            "creada_por",
            "fecha",
            "expires_at",
            "monto_reserva",
            "notas",
            "activa",
            "vencida",
            "estado_reserva",
        )
        read_only_fields = ("id", "fecha", "activa")

    def create(self, validated_data):
        if not validated_data.get("expires_at"):
            validated_data["expires_at"] = timezone.now() + timedelta(hours=72)
        return super().create(validated_data)
    
    def get_vencida(self, obj):
        from django.utils import timezone
        return bool(obj.expires_at and obj.expires_at <= timezone.now())

    def get_estado_reserva(self, obj):
        if not obj.activa:
            return "cancelada"
        return "vencida" if self.get_vencida(obj) else "activa"

    
    
    
    

