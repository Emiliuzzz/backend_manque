from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "rol", "") == "ADMIN")

class IsPropietario(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "rol", "") == "PROPIETARIO")

class IsCliente(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "rol", "") == "CLIENTE")

class PropiedadPermission(BasePermission):

    def has_permission(self, request, view):
        # Lectura para todos
        if request.method in SAFE_METHODS:
            return True

        # Para escribir, debe estar autenticado y ser ADMIN o PROPIETARIO
        if not request.user or not request.user.is_authenticated:
            return False

        return getattr(request.user, "rol", "") in ("ADMIN", "PROPIETARIO")

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        rol = getattr(request.user, "rol", "")

        # ADMIN puede todo
        if rol == "ADMIN":
            return True

        # PROPIETARIO: solo sus propiedades y NO aprobadas (para evitar cambios post-aprobación)
        if rol == "PROPIETARIO":
            return (obj.propietario_user_id == request.user.id) and (not obj.aprobada)

        return False

class NotificacionPermission(BasePermission):
    """
    ADMIN: acceso total.
    Otros: solo sus propias notificaciones.
    """
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "rol", "") == "ADMIN":
            return True
        return obj.usuario_id == getattr(request.user, "id", None)

    def has_permission(self, request, view):
        # Debe estar autenticado para cualquier operación
        return bool(request.user and request.user.is_authenticated)