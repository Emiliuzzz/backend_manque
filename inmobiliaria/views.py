from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse

from rest_framework import viewsets, permissions
from .models import Propietario, Direccion_propietario, Region, Comuna, Propiedad
from .serializers import (PropietarioSerializer, PropietarioDireccionSerializer, RegionSerializer, ComunaSerializer
)


# Create your views here.
class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all().order_by('nombre_region')
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]

class ComunaViewSet(viewsets.ModelViewSet):
    queryset = Comuna.objects.select_related('region').all().order_by('nombre_comuna')
    serializer_class = ComunaSerializer
    permission_classes = [permissions.AllowAny]

class PropietarioViewSet(viewsets.ModelViewSet):
    queryset = Propietario.objects.all().order_by('nombre')
    serializer_class = PropietarioSerializer
    permission_classes = [permissions.AllowAny]

class PropietarioDireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion_propietario.objects.select_related('propietario','comuna','region').all().order_by('principal','-fecha')
    serializer_class = PropietarioDireccionSerializer
    permission_classes = [permissions.AllowAny]




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

  