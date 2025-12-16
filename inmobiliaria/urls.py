from django.urls import path, include
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static

from . import views
from . import views_admin
from .views import (
    # vistas simples
    index,
    about,
    hello,
    propietario,
    propiedad,

    # viewsets para el router
    RegionViewSet,
    ComunaViewSet,
    PropietarioViewSet,
    PropietarioDireccionViewSet,
    InteresadoViewSet,
    PropiedadViewSet,
    VisitaViewSet,
    ReservaViewSet,
    ContratoViewSet,
    PagoViewSet,
    PropiedadFotoViewSet,
    PropiedadDocumentoViewSet,
    CuotaContratoViewSet,
    NotificacionViewSet,
    SolicitudClienteViewSet,

    # vistas de negocio
    RegisterView,
    MisContratosView,
    MisPagosView,
    MisReservasView,
    CatalogoPropiedadesView,
    MisPropiedadesView,
    MiPerfilPropietarioView,
    MiPerfilClienteView,
    MisSolicitudesClienteView
)

router = routers.DefaultRouter()

# Rutas API - catálogos
router.register(r'propietarios', PropietarioViewSet, basename='propietario')
router.register(r'direcciones', PropietarioDireccionViewSet, basename='direccion-propietario')
router.register(r'regiones', RegionViewSet, basename='region')
router.register(r'comunas', ComunaViewSet, basename='comuna')
router.register(r'interesados', InteresadoViewSet, basename='interesado')
router.register(r'propiedades', PropiedadViewSet, basename='propiedad')

# Negocio
router.register(r'visitas', VisitaViewSet, basename='visita')
router.register(r'reservas', ReservaViewSet, basename='reserva')
router.register(r'contratos', ContratoViewSet, basename='contrato')
router.register(r'pagos', PagoViewSet, basename='pago')

# Archivos
router.register(r'propiedad-fotos', PropiedadFotoViewSet, basename='propiedad-foto')
router.register(r'propiedad-documentos', PropiedadDocumentoViewSet, basename='propiedad-documento')

router.register(r'cuotas', CuotaContratoViewSet, basename='cuota')
router.register(r'notificaciones', NotificacionViewSet, basename="notificaciones")
router.register(r"solicitudes-cliente", SolicitudClienteViewSet, basename="solicitud-cliente")

urlpatterns = [
    # páginas simples de prueba
    path('', index),
    path('about/', about),
    path('hello/', hello),
    path('propietario/', propietario),
    path('propiedad/<int:id>/', propiedad),

    # API de usuarios / negocio
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/mis-contratos/', MisContratosView.as_view(), name='mis-contratos'),
    path('api/mis-pagos/', MisPagosView.as_view(), name='mis-pagos'),
    path('api/mis-reservas/', MisReservasView.as_view(), name='mis-reservas'),
    path("api/catalogo/propiedades/", CatalogoPropiedadesView.as_view(), name="catalogo-propiedades"),
    path('api/mis-propiedades/', MisPropiedadesView.as_view(), name='mis-propiedades'),
    path('api/mi-perfil/propietario/', MiPerfilPropietarioView.as_view(), name='mi-perfil-propietario'),
    path('api/mi-perfil/cliente/', MiPerfilClienteView.as_view(), name='mi-perfil-cliente'),
    path('api/mis-solicitudes-cliente/',MisSolicitudesClienteView.as_view(),name='mis-solicitudes-cliente'),
    # 🔹 ENDPOINT RESUMEN ADMIN
    path(
        'api/admin/resumen/',
        views_admin.admin_resumen,         
        name='admin-resumen'
    ),

    # ENDPOINTS ESPECÍFICOS DE ADMIN
    path(
        'api/admin/propietarios/',
        views_admin.AdminPropietarioListCreateView.as_view(),
        name='admin-propietarios'
    ),
        path(
        'api/admin/propietarios/<int:pk>/',
        views_admin.AdminPropietarioRetrieveUpdateView.as_view(),
        name='admin-propietarios-detalle'
    ),

    path(
        'api/admin/propiedades/',
        views_admin.AdminPropiedadListCreateView.as_view(),
        name='admin-propiedades'
    ),
    path(
        'api/admin/propiedades/<int:pk>/',
        views_admin.AdminPropiedadRetrieveUpdateView.as_view(),
        name='admin-propiedad-detalle'
    ),
    path(
        "api/admin/solicitudes-cliente/",
        views_admin.AdminSolicitudClienteListView.as_view(),
        name="admin-solicitudes-cliente-list",
    ),
    path(
        "api/admin/solicitudes-cliente/<int:pk>/",
        views_admin.AdminSolicitudClienteEstadoUpdateView.as_view(),
        name="admin-solicitudes-cliente-update",
    ),
    # API base 
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
