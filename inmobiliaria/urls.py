#from rest_framework import routers
#from .api import 


from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('about/', views.about),
    path('hello/', views.hello),
    path('propietario/', views.propietario),
    path('propiedad/<int:id>', views.propiedad),
]
