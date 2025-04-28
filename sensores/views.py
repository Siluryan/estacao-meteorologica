from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from .models import DadoSensor

@login_required(login_url='login')
def dashboard(request):
    periodo = request.GET.get('periodo', 'hoje')
    hoje = timezone.now()
    
    if periodo == 'hoje':
        dados = DadoSensor.objects.filter(data__date=hoje.date())
    elif periodo == 'semana':
        dados = DadoSensor.objects.filter(data__gte=hoje - timedelta(days=7))
    else:
        dados = DadoSensor.objects.filter(data__gte=hoje - timedelta(days=30))
    
    dados = dados.order_by('-data')[:10]
    return render(request, 'dashboard.html', {'dados': dados})

@login_required(login_url='login')
def estatisticas(request):
    periodo = request.GET.get('periodo', 'hoje')
    hoje = timezone.now()
    
    if periodo == 'hoje':
        dados = DadoSensor.objects.filter(data__date=hoje.date())
    elif periodo == 'semana':
        dados = DadoSensor.objects.filter(data__gte=hoje - timedelta(days=7))
    else:
        dados = DadoSensor.objects.filter(data__gte=hoje - timedelta(days=30))
    
    context = {
        'media_temperatura': round(dados.aggregate(Avg('temperatura'))['temperatura__avg'] or 0, 1),
        'media_umidade': round(dados.aggregate(Avg('umidade'))['umidade__avg'] or 0, 1),
        'media_luminosidade': round(dados.aggregate(Avg('luminosidade'))['luminosidade__avg'] or 0, 1),
        'media_chuva': round(dados.aggregate(Avg('chuva'))['chuva__avg'] or 0, 1),
        'media_corrente': round(dados.aggregate(Avg('corrente'))['corrente__avg'] or 0, 1),
        'media_pm1_0': round(dados.aggregate(Avg('pm1_0'))['pm1_0__avg'] or 0, 1),
        'media_pm2_5': round(dados.aggregate(Avg('pm2_5'))['pm2_5__avg'] or 0, 1),
        'media_pm10': round(dados.aggregate(Avg('pm10'))['pm10__avg'] or 0, 1),
        'deteccoes_gas': dados.filter(gas_detectado=True).count(),
        'total_registros': dados.count(),
    }
    
    if context['total_registros'] > 0:
        context['percentual_gas'] = round((context['deteccoes_gas'] / context['total_registros']) * 100, 1)
    else:
        context['percentual_gas'] = 0
        
    return render(request, 'estatisticas.html', context)