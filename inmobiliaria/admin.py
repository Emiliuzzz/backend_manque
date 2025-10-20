from django import forms
from django.contrib import admin
from .models import *
from .utils import slots_disponibles_para_propiedad

def _choices_from_times(times):
    return [(t.strftime("%H:%M"), t.strftime("%H:%M")) for t in times]

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
admin.site.register(Propietario)
admin.site.register(Propiedad)
admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Direccion_propietario)
admin.site.register(Interesado)
admin.site.register(Reserva)
admin.site.register(Contrato)
admin.site.register(Pago)
admin.site.register(PropiedadFoto)
admin.site.register(PropiedadDocumento)

