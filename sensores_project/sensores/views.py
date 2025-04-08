from django.shortcuts import render
from .models import DadoSensor

def dashboard(request):
    dados = DadoSensor.objects.order_by('-data')[:10]
    return render(request, 'dashboard.html', {'dados': dados})
