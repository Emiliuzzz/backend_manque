from rest_framework import generics, permissions

from .models import Propietario, Propiedad
from .serializers import (
    AdminPropietarioSerializer,
    AdminPropiedadSerializer,
)
from .permisssions_roles import IsAdmin  

from rest_framework.decorators import api_view, permission_classes

from rest_framework.response import Response
from inmobiliaria.models import Propiedad, Propietario

@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_resumen(request):
    data = {
        "total_propiedades": Propiedad.objects.count(),
        "total_propietarios": Propietario.objects.count(),
    }
    return Response(data)

class AdminPropietarioListCreateView(generics.ListCreateAPIView):
    queryset = Propietario.objects.all().order_by('primer_apellido', 'primer_nombre')
    serializer_class = AdminPropietarioSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class AdminPropiedadListCreateView(generics.ListCreateAPIView):
    queryset = Propiedad.objects.select_related('propietario').all().order_by('-id')
    serializer_class = AdminPropiedadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
