import django_filters as df
from .models import Propiedad

class PropiedadFilter(df.FilterSet):
    precio_min = df.NumberFilter(field_name="precio", lookup_expr="gte")
    precio_max = df.NumberFilter(field_name="precio", lookup_expr="lte")
    dormitorios_min = df.NumberFilter(field_name="dormitorios", lookup_expr="gte")
    banos_min = df.NumberFilter(field_name="banos", lookup_expr="gte")  
    ciudad = df.CharFilter(field_name="ciudad", lookup_expr="icontains")
    tipo = df.CharFilter(field_name="tipo", lookup_expr="iexact")       
    estado = df.CharFilter(field_name="estado", lookup_expr="iexact")   

    
    orientacion = df.CharFilter(field_name="orientacion", lookup_expr="iexact")

    class Meta:
        model = Propiedad
        fields = ["tipo", "estado", "ciudad", "orientacion"]