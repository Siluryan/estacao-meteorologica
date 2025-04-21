from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('estatisticas/', views.estatisticas, name='estatisticas'),
]