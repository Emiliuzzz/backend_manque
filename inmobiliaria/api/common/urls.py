from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("token/", views.CustomTokenObtainPairView.as_view(), name="token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    path("catalogo/propiedades/", views.CatalogoPropiedadesView.as_view(), name="catalogo-propiedades"),

    path("mis-contratos/", views.MisContratosView.as_view(), name="mis-contratos"),
    path("mis-pagos/", views.MisPagosView.as_view(), name="mis-pagos"),
    path("mis-reservas/", views.MisReservasView.as_view(), name="mis-reservas"),
    path("cambiar-password/", views.CambiarPasswordView.as_view()),
]
