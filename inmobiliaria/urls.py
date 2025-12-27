from django.urls import path, include
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    index, about, hello, propietario, propiedad,

    RegionViewSet, ComunaViewSet, PropietarioViewSet, PropietarioDireccionViewSet,
    InteresadoViewSet, PropiedadViewSet, VisitaViewSet, ReservaViewSet,
    ContratoViewSet, PagoViewSet, PropiedadFotoViewSet, PropiedadDocumentoViewSet,
    CuotaContratoViewSet, NotificacionViewSet, SolicitudClienteViewSet,
)

router = routers.DefaultRouter()

# Router (uso común / público)
router.register(r'propietarios', PropietarioViewSet, basename='propietario')
router.register(r'direcciones', PropietarioDireccionViewSet, basename='direccion-propietario')
router.register(r'regiones', RegionViewSet, basename='region')
router.register(r'comunas', ComunaViewSet, basename='comuna')
router.register(r'interesados', InteresadoViewSet, basename='interesado')
router.register(r'propiedades', PropiedadViewSet, basename='propiedad')

router.register(r'visitas', VisitaViewSet, basename='visita')
router.register(r'reservas', ReservaViewSet, basename='reserva')
router.register(r'contratos', ContratoViewSet, basename='contrato')
router.register(r'pagos', PagoViewSet, basename='pago')

router.register(r'propiedad-fotos', PropiedadFotoViewSet, basename='propiedad-foto')
router.register(r'propiedad-documentos', PropiedadDocumentoViewSet, basename='propiedad-documento')

router.register(r'cuotas', CuotaContratoViewSet, basename='cuota')
router.register(r'notificaciones', NotificacionViewSet, basename="notificaciones")
router.register(r'solicitudes-cliente', SolicitudClienteViewSet, basename="solicitud-cliente")

urlpatterns = [
    # Debug / demo
    path('', index),
    path('about/', about),
    path('hello/', hello),
    path('propietario/', propietario),
    path('propiedad/<int:id>/', propiedad),

    #  Common
    path('api/', include('inmobiliaria.api.common.urls')),

    #  Cliente
    path('api/cliente/', include('inmobiliaria.api.cliente.urls')),

    #  Propietario
    path('api/propietario/', include('inmobiliaria.api.propietario.urls')),

    #  Admin
    path('api/admin/', include('inmobiliaria.api.admin.urls')),

    # Router base
    path('api/', include(router.urls)),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
