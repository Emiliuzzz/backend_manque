from rest_framework import serializers
from inmobiliaria.models import *
from inmobiliaria.validators import *
from inmobiliaria.config import *
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from datetime import timedelta
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

User = get_user_model()

class AdminPropietarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propietario
        fields = [
            "id",
            "primer_nombre",
            "segundo_nombre",
            "primer_apellido",
            "segundo_apellido",
            "rut",
            "telefono",
            "email",
        ]

    def validate_rut(self, value):
        v = normalizar_rut(value)
        validar_rut(v)
        return v

    def validate_telefono(self, value):
        if value:
            validar_telefono_cl(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        email = (validated_data.get("email") or "").strip().lower()
        rut = validated_data.get("rut") or ""

        if not email:
            raise serializers.ValidationError(
                {"email": "El email es obligatorio para crear la cuenta."}
            )

        rut_norm = normalizar_rut(rut)

        propietario = Propietario.objects.create(**validated_data)

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                "email": email,
                "rol": "PROPIETARIO",
                "aprobado": True,
                "is_active": True,
            },
        )

        user.email = email
        user.rol = "PROPIETARIO"
        if hasattr(user, "aprobado"):
            user.aprobado = True
        user.is_active = True

        user.set_password(rut_norm)
        user.save()
        propietario.usuario = user
        propietario.save(update_fields=["usuario"])


        return propietario


class AdminPropietarioBasicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propietario
        fields = [
            'id',
            'primer_nombre',
            'segundo_nombre',
            'primer_apellido',
            'segundo_apellido',
            'rut',
            'email',
        ]


class AdminPropiedadSerializer(serializers.ModelSerializer):
    propietario = AdminPropietarioBasicoSerializer(read_only=True)
    propietario_id = serializers.PrimaryKeyRelatedField(
        source='propietario',
        queryset=Propietario.objects.all(),
        write_only=True,
        required=False,  
    )

    class Meta:
        model = Propiedad
        fields = [
            'id',
            'propietario',
            'propietario_id',
            'titulo',
            'direccion',
            'ciudad',
            'descripcion',
            'tipo',
            'dormitorios',
            'baos',
            'metros2',
            'precio',
            'estado',
            'estado_aprobacion',
            'orientacion',
        ]
  

class AdminUsuarioSerializer(serializers.ModelSerializer):
    perfil = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "rol",
            "is_active",
            "aprobado",
            "perfil",
        ]

    def get_perfil(self, obj):
        email = (obj.email or "").strip().lower()

        # ---- PROPIETARIO ----
        p = Propietario.objects.filter(email__iexact=email).first()
        if p:
            dir_p = (
                p.direcciones.filter(principal=True)
                .select_related("comuna", "region")
                .first()
            )

            direccion_data = None
            if dir_p:
                direccion_data = {
                    "id": dir_p.id,
                    "calle_o_pasaje": dir_p.calle_o_pasaje or "",
                    "numero": dir_p.numero or "",
                    "poblacion_o_villa": dir_p.poblacion_o_villa or "",
                    "comuna_id": dir_p.comuna_id,
                    "region_id": dir_p.region_id,
                    "comuna_nombre": dir_p.comuna.nombre_comuna if dir_p.comuna else "",
                    "region_nombre": dir_p.region.nombre_region if dir_p.region else "",
                    "referencia": dir_p.referencia or "",
                    "codigo_postal": dir_p.codigo_postal or "",
                }

            return {
                "tipo": "PROPIETARIO",
                "id": p.id,
                "nombre": f"{p.primer_nombre} {p.primer_apellido}".strip(),
                "rut": p.rut,
                "telefono": p.telefono,
                "email": p.email,
                "primer_nombre": p.primer_nombre,
                "segundo_nombre": p.segundo_nombre,
                "primer_apellido": p.primer_apellido,
                "segundo_apellido": p.segundo_apellido,
                "direccion_principal": direccion_data,
            }

        # ---- CLIENTE / INTERESADO ----
        c = Interesado.objects.filter(email__iexact=email).first()
        if c:
            return {
                "tipo": "CLIENTE",
                "id": c.id,
                "nombre": f"{c.primer_nombre} {c.primer_apellido}".strip(),
                "rut": c.rut,
                "telefono": c.telefono,
                "email": c.email,
                "primer_nombre": c.primer_nombre,
                "segundo_nombre": c.segundo_nombre,
                "primer_apellido": c.primer_apellido,
                "segundo_apellido": c.segundo_apellido,
                "direccion_principal": None,
            }

        # ---- SIN PERFIL ----
        return None


class AdminUsuarioUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    rol = serializers.ChoiceField(choices=["ADMIN", "PROPIETARIO", "CLIENTE"], required=False)
    is_active = serializers.BooleanField(required=False)
    aprobado = serializers.BooleanField(required=False)

    primer_nombre = serializers.CharField(required=False, allow_blank=True)
    segundo_nombre = serializers.CharField(required=False, allow_blank=True)
    primer_apellido = serializers.CharField(required=False, allow_blank=True)
    segundo_apellido = serializers.CharField(required=False, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_blank=True)

    rut = serializers.CharField(required=False)

    def validate(self, attrs):
        if "rut" in attrs:
            raise serializers.ValidationError({"rut": "El RUT no se puede modificar."})
        return attrs


class AdminUsuarioCrearPerfilSerializer(serializers.Serializer):
    primer_nombre = serializers.CharField(required=False, allow_blank=True)
    segundo_nombre = serializers.CharField(required=False, allow_blank=True)
    primer_apellido = serializers.CharField(required=False, allow_blank=True)
    segundo_apellido = serializers.CharField(required=False, allow_blank=True)
    rut = serializers.CharField(required=True)
    telefono = serializers.CharField(required=True)
    fecha_registro = serializers.DateTimeField(required=False)

    def validate_rut(self, value):
        v = normalizar_rut(value)
        validar_rut(v)
        return v

    def validate_telefono(self, value):
        validar_telefono_cl(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["user"]
        email = (user.email or "").strip().lower()
        if not email:
            raise serializers.ValidationError({"email": "El usuario no tiene email."})

        rut_norm = validated_data["rut"]
        telefono = validated_data["telefono"]
        fecha_registro = validated_data.get("fecha_registro") or timezone.now()

        # Si es PROPIETARIO -> crear Propietario si no existe
        if user.rol == "PROPIETARIO":
            if Propietario.objects.filter(usuario=user).exists() or Propietario.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError({"detail": "Ya existe perfil Propietario para este usuario."})

            p = Propietario.objects.create(
                primer_nombre=validated_data.get("primer_nombre",""),
                segundo_nombre=validated_data.get("segundo_nombre",""),
                primer_apellido=validated_data.get("primer_apellido",""),
                segundo_apellido=validated_data.get("segundo_apellido",""),
                rut=rut_norm,
                telefono=telefono,
                email=email,
                usuario=user,
            )
            return p

        # Si es CLIENTE -> crear Interesado si no existe
        if user.rol == "CLIENTE":
            if Interesado.objects.filter(usuario=user).exists() or Interesado.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError({"detail": "Ya existe perfil Cliente para este usuario."})

            c = Interesado.objects.create(
                primer_nombre=validated_data.get("primer_nombre",""),
                segundo_nombre=validated_data.get("segundo_nombre",""),
                primer_apellido=validated_data.get("primer_apellido",""),
                segundo_apellido=validated_data.get("segundo_apellido",""),
                rut=rut_norm,
                telefono=telefono,
                email=email,
                fecha_registro=fecha_registro,
                usuario=user,
            )
            return c

        raise serializers.ValidationError({"detail": "El rol del usuario no permite crear perfil."})
    

class AdminUsuarioCreateSerializer(serializers.Serializer):
    # -------- Cuenta --------
    email = serializers.EmailField()
    rol = serializers.ChoiceField(choices=["ADMIN", "PROPIETARIO", "CLIENTE"])
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)

    is_active = serializers.BooleanField(default=True)
    aprobado = serializers.BooleanField(default=True)

    # -------- Perfil (común) --------
    primer_nombre = serializers.CharField(required=False, allow_blank=True)
    segundo_nombre = serializers.CharField(required=False, allow_blank=True)
    primer_apellido = serializers.CharField(required=False, allow_blank=True)
    segundo_apellido = serializers.CharField(required=False, allow_blank=True)
    rut = serializers.CharField(required=False, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_blank=True)

    # Dirección solo para PROPIETARIO (opcional)
    calle = serializers.CharField(required=False, allow_blank=True)
    numero = serializers.CharField(required=False, allow_blank=True)
    poblacion_o_villa = serializers.CharField(required=False, allow_blank=True)
    comuna_id = serializers.IntegerField(required=False)
    region_id = serializers.IntegerField(required=False)
    referencia = serializers.CharField(required=False, allow_blank=True)
    codigo_postal = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        rol = (attrs.get("rol") or "").upper()

        if rol in ["CLIENTE", "PROPIETARIO"]:
            if not attrs.get("rut"):
                raise serializers.ValidationError({"rut": "El RUT es obligatorio."})
            if not attrs.get("telefono"):
                raise serializers.ValidationError({"telefono": "El teléfono es obligatorio."})
            if not attrs.get("primer_nombre"):
                raise serializers.ValidationError({"primer_nombre": "El primer nombre es obligatorio."})
            if not attrs.get("primer_apellido"):
                raise serializers.ValidationError({"primer_apellido": "El primer apellido es obligatorio."})

            # Validaciones CL
            rut_norm = normalizar_rut(attrs["rut"])
            validar_rut(rut_norm)
            attrs["rut"] = rut_norm

            validar_telefono_cl(attrs["telefono"])
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = (validated_data.get("email") or "").strip().lower()
        rol = (validated_data.get("rol") or "").upper()
        password = (validated_data.get("password") or "").strip()

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                "email": email,
                "rol": rol,
                "is_active": validated_data.get("is_active", True),
                "aprobado": validated_data.get("aprobado", True),
            },
        )

        user.email = email
        user.username = email
        user.rol = rol
        user.is_active = validated_data.get("is_active", True)
        if hasattr(user, "aprobado"):
            user.aprobado = validated_data.get("aprobado", True)

        if not password and rol in ["CLIENTE", "PROPIETARIO"]:
            password = validated_data.get("rut") or ""
        if password:
            user.set_password(password)
        user.save()

        # ------- Crear perfil según rol -------
        if rol == "CLIENTE":
            Interesado.objects.create(
                primer_nombre=validated_data.get("primer_nombre", ""),
                segundo_nombre=validated_data.get("segundo_nombre", ""),
                primer_apellido=validated_data.get("primer_apellido", ""),
                segundo_apellido=validated_data.get("segundo_apellido", ""),
                rut=validated_data.get("rut", ""),
                telefono=validated_data.get("telefono", ""),
                email=email,
                usuario=user,
            )

        elif rol == "PROPIETARIO":
            perfil = Propietario.objects.create(
                primer_nombre=validated_data.get("primer_nombre", ""),
                segundo_nombre=validated_data.get("segundo_nombre", ""),
                primer_apellido=validated_data.get("primer_apellido", ""),
                segundo_apellido=validated_data.get("segundo_apellido", ""),
                rut=validated_data.get("rut", ""),
                telefono=validated_data.get("telefono", ""),
                email=email,
                usuario=user,
            )

            # Crear dirección principal si viene info mínima
            calle = validated_data.get("calle") or ""
            numero = validated_data.get("numero") or ""
            comuna_id = validated_data.get("comuna_id")
            region_id = validated_data.get("region_id")

            if calle and numero and comuna_id and region_id:
                Direccion_propietario.objects.create(
                    propietario=perfil,
                    calle_o_pasaje=calle,
                    numero=numero,
                    poblacion_o_villa=validated_data.get("poblacion_o_villa", ""),
                    comuna_id=comuna_id,
                    region_id=region_id,
                    referencia=validated_data.get("referencia", ""),
                    codigo_postal=validated_data.get("codigo_postal", ""),
                    principal=True,
                )

        # ADMIN no tiene perfil
        return user
