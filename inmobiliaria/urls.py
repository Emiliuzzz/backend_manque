#from rest_framework import routers
#from .api import 


from django.urls import path, include
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from . import views

from .views import *      


router = routers.DefaultRouter()

# Rutas API
# Catálogos
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
router.register(r'propiedad-fotos', PropiedadViewSet, basename='propiedad-foto')
router.register(r'propiedad-documentos', PropiedadDocumentoViewSet, basename='propiedad-documento')

router.register(r'cuotas', CuotaContratoViewSet, basename='cuota')
router.register(r'notificaciones', NotificacionViewSet, basename="notificaciones")


urlpatterns = [
    path('', views.index),
    path('about/', views.about),
    path('hello/', views.hello),
    path('propietario/', views.propietario),
    path('propiedad/<int:id>/', views.propiedad),

    path('api/registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('api/', include(router.urls)),
    path('api/mis-contratos/', MisContratosView.as_view(), name='mis-contratos'),
    path('api/mis-pagos/',     MisPagosView.as_view(),     name='mis-pagos'),
    path('api/mis-reservas/',  MisReservasView.as_view(),  name='mis-reservas'),
    path("api/catalogo/propiedades/", CatalogoPropiedadesView.as_view(), name="catalogo-propiedades"),
    # API base
    path('api/', include(router.urls)),
]


'''
urlpatterns = [
    path('', views.index),
    path('about/', views.about),
    path('hello/', views.hello),
    path('propietario/', views.propietario),
    path('propiedad/<int:id>', views.propiedad),
    
]
'''