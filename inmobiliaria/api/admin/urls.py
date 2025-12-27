from django.urls import path
from .views import (
    admin_resumen,
    admin_usuarios_list,
    admin_usuario_detail,
    admin_usuario_desactivar,
    admin_usuario_activar,
    AdminPropietarioListCreateView,
    AdminPropietarioRetrieveUpdateView,
    AdminPropiedadListCreateView,
    AdminPropiedadRetrieveUpdateView,
    AdminSolicitudClienteListView,
    AdminSolicitudClienteEstadoUpdateView,
    admin_usuario_crear_perfil
)

urlpatterns = [
    path("resumen/", admin_resumen),
    path("propietarios/", AdminPropietarioListCreateView.as_view()),
    path("propietarios/<int:pk>/", AdminPropietarioRetrieveUpdateView.as_view()),
    path("propiedades/", AdminPropiedadListCreateView.as_view()),
    path("propiedades/<int:pk>/", AdminPropiedadRetrieveUpdateView.as_view()),
    path("solicitudes-cliente/", AdminSolicitudClienteListView.as_view()),
    path("solicitudes-cliente/<int:pk>/", AdminSolicitudClienteEstadoUpdateView.as_view()),
    path("usuarios/", admin_usuarios_list),
    path("usuarios/<int:pk>/", admin_usuario_detail),
    path("usuarios/<int:pk>/crear-perfil/", admin_usuario_crear_perfil),
    path("usuarios/<int:pk>/desactivar/", admin_usuario_desactivar),
    path("usuarios/<int:pk>/activar/", admin_usuario_activar),
    

]
