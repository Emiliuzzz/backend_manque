from django.urls import path
from . import views

urlpatterns = [
    path("mi-perfil/", views.MiPerfilPropietarioView.as_view(), name="propietario-mi-perfil"),
    path("mis-propiedades/", views.MisPropiedadesPropietarioView.as_view(), name="propietario-mis-propiedades"),
    path("mis-reservas/", views.MisReservasPropietarioView.as_view(), name="propietario-mis-reservas"),
    path("mis-contratos/", views.MisContratosPropietarioView.as_view(), name="propietario-mis-contratos"),
    path("mis-pagos/", views.MisPagosPropietarioView.as_view(), name="propietario-mis-pagos"),
]
