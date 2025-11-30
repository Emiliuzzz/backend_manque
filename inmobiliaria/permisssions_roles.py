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
        # Lecturas siempre permitidas
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        rol = getattr(user, "rol", "")

        # Admin puede hacer todo
        if rol == "ADMIN":
            return True

        # Propietario puede crear y actualizar
        if rol == "PROPIETARIO" and view.action in ["create", "update", "partial_update"]:
            return True


        return False

    def has_object_permission(self, request, view, obj):
        # Lecturas permitidas
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        rol = getattr(user, "rol", "")

        # Admin siempre puede
        if rol == "ADMIN":
            return True

        # Propietario solo puede modificar sus propias propiedades
        if rol == "PROPIETARIO":
            return obj.propietario_user_id == user.id

        return False

class NotificacionPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "rol", "") == "ADMIN":
            return True
        return obj.usuario_id == getattr(request.user, "id", None)

    def has_permission(self, request, view):
        # Debe estar autenticado para cualquier operación
        return bool(request.user and request.user.is_authenticated)