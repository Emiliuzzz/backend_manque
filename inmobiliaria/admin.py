from django.contrib import admin
from .models import Propietario, Propiedad,  Region, Comuna, Direccion_propietario
# Register your models here.

admin.site.register(Propietario)
admin.site.register(Propiedad)
admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Direccion_propietario)