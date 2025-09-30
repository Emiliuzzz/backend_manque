from rest_framework import serializers
from .models import Propietario, Direccion_propietario, Region, Comuna

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
        fields = ['id','nombre','rut','telefono','email','direcciones']