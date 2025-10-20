from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse


from datetime import datetime
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from .config import *
from .utils import * 


# Create your views here.


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



class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all().order_by('nombre_region')
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]

class ComunaViewSet(viewsets.ModelViewSet):
    queryset = Comuna.objects.select_related('region').all().order_by('nombre_comuna')
    serializer_class = ComunaSerializer
    permission_classes = [permissions.AllowAny]

class PropietarioViewSet(viewsets.ModelViewSet):
    queryset = Propietario.objects.all().order_by('primer_nombre')
    serializer_class = PropietarioSerializer
    permission_classes = [permissions.AllowAny]

class PropietarioDireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion_propietario.objects.select_related('propietario','comuna','region').all().order_by('principal','-fecha')
    serializer_class = PropietarioDireccionSerializer
    permission_classes = [permissions.AllowAny]

class InteresadoViewSet(viewsets.ModelViewSet):
    queryset = Interesado.objects.all().order_by('-id')
    serializer_class = InteresadoSerializer
    permission_classes = [permissions.AllowAny]


class VisitaViewSet(viewsets.ModelViewSet):
    queryset = Visita.objects.all().order_by("-id")
    serializer_class = VisitaSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["GET"], url_path="slots")
    def slots(self, request):
        prop_id = request.query_params.get("propiedad")
        fecha_str = request.query_params.get("fecha")
        if not prop_id or not fecha_str:
            return Response({"detail": "Falta propiedad o fecha"}, status=400)
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Formato de fecha inválido (YYYY-MM-DD)"}, status=400)

        libres = slots_disponibles_para_propiedad(int(prop_id), fecha)
        return Response([h.strftime("%H:%M") for h in libres], status=200)

    @action(detail=False, methods=["GET"], url_path="agenda")
    def agenda(self, request):
        prop_id = request.query_params.get("propiedad")
        if not prop_id:
            return Response({"detail": "Falta propiedad"}, status=400)

        start_str = request.query_params.get("start")
        days_str = request.query_params.get("days")

        start = None
        if start_str:
            try:
                start = datetime.strptime(start_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"detail": "start inválido, use YYYY-MM-DD"}, status=400)

        days = DEFAULT_DAYS_PAGE
        if days_str:
            try:
                days = int(days_str)
            except ValueError:
                pass
        if days < 1:
            days = 1
        if days > MAX_DAYS_PAGE:
            days = MAX_DAYS_PAGE

        data = generar_agenda_disponible(int(prop_id), start_date=start, days=days)
        return Response(data, status=200)
    





class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all().order_by("-fecha")
    serializer_class = ReservaSerializer
    permission_classes = [permissions.AllowAny]

class ContratoViewSet(viewsets.ModelViewSet):
    queryset = Contrato.objects.all().order_by("-fecha_firma")
    serializer_class = ContratoSerializer
    permission_classes = [permissions.AllowAny]

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all().order_by("-fecha")
    serializer_class = PagoSerializer
    permission_classes = [permissions.AllowAny]

class PropiedadFotoViewSet(viewsets.ModelViewSet):
    queryset = PropiedadFoto.objects.all().order_by("propiedad","orden")
    serializer_class = PropiedadFotoSerializer
    permission_classes = [permissions.AllowAny]

class PropiedadDocumentoViewSet(viewsets.ModelViewSet):
    queryset = PropiedadDocumento.objects.all().order_by("-subido")
    serializer_class = PropiedadDocumentoSerializer
    permission_classes = [permissions.AllowAny]


  