"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from inmobiliaria import views

router = routers.DefaultRouter()
router.register(r'propietarios', views.PropietarioViewSet)
router.register(r'direcciones', views.PropietarioDireccionViewSet)
router.register(r'regiones', views.RegionViewSet)
router.register(r'comunas', views.ComunaViewSet)
router.register(r'interesados', views.InteresadoViewSet)
router.register(r'visitas', views.VisitaViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('', include('inmobiliaria.urls'))
]   
