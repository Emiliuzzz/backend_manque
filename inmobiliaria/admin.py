from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from .utils import slots_disponibles_para_propiedad

def _choices_from_times(times):
    return [(t.strftime("%H:%M"), t.strftime("%H:%M")) for t in times]


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "aprobado", "is_active", "is_staff", "is_superuser")
    list_filter  = ("rol", "aprobado", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        ("Rol y aprobación", {"fields": ("rol", "aprobado")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Rol y aprobación", {"fields": ("rol", "aprobado")}),
    )

# --- Acciones ---

@admin.action(description="Aprobar propiedades seleccionadas")
def aprobar_propiedades(modeladmin, request, queryset):
    updated = queryset.update(aprobada=True)
    modeladmin.message_user(request, f"{updated} propiedades aprobadas.")

@admin.action(description="Marcar notificaciones como leídas")
def marcar_leidas(modeladmin, request, queryset):
    updated = queryset.update(leida=True)
    modeladmin.message_user(request, f"{updated} notificaciones marcadas como leídas.")

# --- Admin de Propiedad ---

@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "ciudad", "tipo", "estado", "aprobada", "propietario_user")
    list_filter  = ("aprobada", "estado", "tipo", "ciudad")
    search_fields = ("titulo", "ciudad", "propietario__rut", "propietario__primer_nombre")
    list_display_links = ("titulo",)  # <— asegura el link a la vista de edición
    actions = [aprobar_propiedades]

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser or getattr(request.user, "rol", "") == "ADMIN":
            return True

        if obj is None:
            return super().has_change_permission(request, obj)

        # Propietario: puede editar SOLO si es el dueño y NO está aprobada
        if getattr(request.user, "rol", "") == "PROPIETARIO":
            return (obj.propietario_user_id == request.user.id) and (not obj.aprobada)

        return False

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or getattr(request.user, "rol", "") == "ADMIN":
            return super().get_readonly_fields(request, obj)

        # Propietario: si ya está aprobada, deja todo en solo lectura
        if getattr(request.user, "rol", "") == "PROPIETARIO" and obj and obj.aprobada:
            return [f.name for f in self.model._meta.fields] + [m.name for m in self.model._meta.many_to_many]

        return super().get_readonly_fields(request, obj)
    

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "tipo", "titulo", "leida", "created_at")
    list_filter = ("tipo", "leida", "created_at")
    search_fields = ("titulo", "mensaje", "usuario__username", "usuario__email")
    actions = [marcar_leidas]

class VisitaAdminForm(forms.ModelForm):
    class Meta:
        model = Visita
        fields = "__all__"
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        propiedad_id = self.instance.propiedad_id if (self.instance and self.instance.pk) else None
        fecha = getattr(self.instance, "fecha", None)

        data = self.data or self.initial
        prop_str = data.get("propiedad") or self.initial.get("propiedad")
        if prop_str:
            try:
                propiedad_id = int(prop_str)
            except Exception:
                pass

        fecha_str = data.get("fecha") or self.initial.get("fecha")
        if fecha_str:
            from datetime import datetime
            try:
                fecha = datetime.strptime(str(fecha_str), "%Y-%m-%d").date()
            except Exception:
                fecha = None

        disponibles = slots_disponibles_para_propiedad(propiedad_id, fecha)
        self.fields["hora"].widget = forms.Select(choices=_choices_from_times(disponibles))
        self.fields["hora"].help_text = (
            "Selecciona un horario disponible."
            if (propiedad_id and fecha) else
            "Primero elige Propiedad y Fecha para ver solo los horarios disponibles."
        )

@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    form = VisitaAdminForm
    list_display = ("propiedad", "interesado", "fecha", "hora", "estado")
    list_filter = ("estado", "fecha", "hora")


@admin.register(SolicitudCliente)
class SolicitudClienteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'interesado', 'tipo_operacion', 'tipo_propiedad',
        'ciudad', 'comuna', 'estado', 'created_at'
    )
    search_fields = ('interesado__primer_nombre', 'interesado__rut', 'ciudad', 'comuna')
    list_filter = ('estado', 'tipo_operacion', 'tipo_propiedad', 'ciudad')
    ordering = ('-created_at',)

    

admin.site.register(Propietario) 
admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Direccion_propietario)
admin.site.register(Interesado)
admin.site.register(Reserva)
admin.site.register(Contrato)
admin.site.register(Historial)
admin.site.register(Pago)
admin.site.register(PropiedadFoto)
admin.site.register(PropiedadDocumento)

