from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone
import json
from .models import DadoSensor
from django.db.models.functions import TruncDate


@login_required(login_url="login")
def dashboard(request):
    periodo = request.GET.get("periodo", "hoje")
    hoje_local = timezone.localtime(timezone.now())
    inicio_hoje_local = hoje_local.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_hoje_local = hoje_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    utc = dt_timezone.utc
    inicio_hoje_utc = inicio_hoje_local.astimezone(utc)
    fim_hoje_utc = fim_hoje_local.astimezone(utc)

    if periodo == "hoje":
        dados = DadoSensor.objects.filter(data__gte=inicio_hoje_utc, data__lte=fim_hoje_utc)
    elif periodo == "semana":
        inicio_local = inicio_hoje_local - timedelta(days=7)
        inicio_utc = inicio_local.astimezone(utc)
        dados = DadoSensor.objects.filter(data__gte=inicio_utc)
    else:
        inicio_local = inicio_hoje_local - timedelta(days=30)
        inicio_utc = inicio_local.astimezone(utc)
        dados = DadoSensor.objects.filter(data__gte=inicio_utc)

    dados = dados.order_by("-data")[:10]
    return render(request, "dashboard.html", {"dados": dados})


@login_required(login_url="login")
def estatisticas(request):
    periodo = request.GET.get("periodo", "hoje")
    hoje_local = timezone.localtime(timezone.now())
    inicio_hoje_local = hoje_local.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_hoje_local = hoje_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    utc = dt_timezone.utc
    inicio_hoje_utc = inicio_hoje_local.astimezone(utc)
    fim_hoje_utc = fim_hoje_local.astimezone(utc)

    if periodo == "hoje":
        dados = DadoSensor.objects.filter(data__gte=inicio_hoje_utc, data__lte=fim_hoje_utc)
    elif periodo == "semana":
        inicio_local = inicio_hoje_local - timedelta(days=6)
        inicio_utc = inicio_local.astimezone(utc)
        dados = DadoSensor.objects.filter(data__gte=inicio_utc, data__lte=fim_hoje_utc)
    else:
        inicio_local = inicio_hoje_local - timedelta(days=29)
        inicio_utc = inicio_local.astimezone(utc)
        dados = DadoSensor.objects.filter(data__gte=inicio_utc, data__lte=fim_hoje_utc)

    context = {
        "periodo": periodo,
        "media_temperatura": round(
            dados.aggregate(Avg("temperatura"))["temperatura__avg"] or 0, 1
        ),
        "media_umidade": round(dados.aggregate(Avg("umidade"))["umidade__avg"] or 0, 1),
        "media_luminosidade": round(
            dados.aggregate(Avg("luminosidade"))["luminosidade__avg"] or 0, 1
        ),
        "media_chuva": round(dados.aggregate(Avg("chuva"))["chuva__avg"] or 0, 1),
        "media_corrente": round(
            dados.aggregate(Avg("corrente"))["corrente__avg"] or 0, 1
        ),
        "media_pm1_0": round(dados.aggregate(Avg("pm1_0"))["pm1_0__avg"] or 0, 1),
        "media_pm2_5": round(dados.aggregate(Avg("pm2_5"))["pm2_5__avg"] or 0, 1),
        "media_pm10": round(dados.aggregate(Avg("pm10"))["pm10__avg"] or 0, 1),
        "media_vento_kmh": round(
            dados.aggregate(Avg("vento_kmh"))["vento_kmh__avg"] or 0, 1
        ),
        "media_umidade_solo": round(
            dados.aggregate(Avg("umidade_solo_pct"))["umidade_solo_pct__avg"] or 0, 1
        ),
        "media_pressao": round(
            dados.aggregate(Avg("pressao_hpa"))["pressao_hpa__avg"] or 0, 1
        ),
        "media_altitude": round(
            dados.aggregate(Avg("altitude_m"))["altitude_m__avg"] or 0, 1
        ),
        "media_temp_bmp": round(
            dados.aggregate(Avg("temperatura_bmp"))["temperatura_bmp__avg"] or 0, 1
        ),
        "deteccoes_gas": dados.filter(gas_detectado=True).count(),
        "total_registros": dados.count(),
    }

    if dados.exists():
        max_temp_registro = dados.order_by("-temperatura").first()
        context["max_temperatura"] = round(max_temp_registro.temperatura, 1)
        context["max_temperatura_data"] = timezone.localtime(
            max_temp_registro.data
        ).strftime("%d/%m/%Y %H:%M")

        min_temp_registro = dados.order_by("temperatura").first()
        context["min_temperatura"] = round(min_temp_registro.temperatura, 1)
        context["min_temperatura_data"] = timezone.localtime(
            min_temp_registro.data
        ).strftime("%d/%m/%Y %H:%M")

        max_umidade_registro = dados.order_by("-umidade").first()
        context["max_umidade"] = round(max_umidade_registro.umidade, 1)
        context["max_umidade_data"] = timezone.localtime(
            max_umidade_registro.data
        ).strftime("%d/%m/%Y %H:%M")

        min_umidade_registro = dados.order_by("umidade").first()
        context["min_umidade"] = round(min_umidade_registro.umidade, 1)
        context["min_umidade_data"] = timezone.localtime(
            min_umidade_registro.data
        ).strftime("%d/%m/%Y %H:%M")

    if context["total_registros"] > 0:
        context["percentual_gas"] = round(
            (context["deteccoes_gas"] / context["total_registros"]) * 100, 1
        )
    else:
        context["percentual_gas"] = 0

    dados_temperatura = {
        "hoje": {"labels": [], "data": []},
        "semana": {"labels": [], "data": []},
        "mes": {"labels": [], "data": []},
    }
    dados_umidade = {
        "hoje": {"labels": [], "data": []},
        "semana": {"labels": [], "data": []},
        "mes": {"labels": [], "data": []},
    }
    dados_particulas = {
        "hoje": {"labels": [], "data": {"pm1_0": [], "pm2_5": [], "pm10": []}},
        "semana": {"labels": [], "data": {"pm1_0": [], "pm2_5": [], "pm10": []}},
        "mes": {"labels": [], "data": {"pm1_0": [], "pm2_5": [], "pm10": []}},
    }

    ultima_localizacao = (
        dados.exclude(localizacao__isnull=True).order_by("-data").first()
    )

    if ultima_localizacao:
        context["ultima_latitude"] = ultima_localizacao.latitude
        context["ultima_longitude"] = ultima_localizacao.longitude
        context["ultima_localizacao"] = ultima_localizacao.localizacao

    if periodo == "hoje":
        dados_ordenados = dados.order_by("data")
        for dado in dados_ordenados:
            label = timezone.localtime(dado.data).strftime("%H:%M")
            dados_temperatura["hoje"]["labels"].append(label)
            dados_temperatura["hoje"]["data"].append(dado.temperatura)
            dados_umidade["hoje"]["labels"].append(label)
            dados_umidade["hoje"]["data"].append(dado.umidade)
            dados_particulas["hoje"]["labels"].append(label)
            dados_particulas["hoje"]["data"]["pm1_0"].append(dado.pm1_0)
            dados_particulas["hoje"]["data"]["pm2_5"].append(dado.pm2_5)
            dados_particulas["hoje"]["data"]["pm10"].append(dado.pm10)

    else:
        agrupados = (
            dados.annotate(dia=TruncDate("data"))
            .values("dia")
            .annotate(
                temp_avg=Avg("temperatura"),
                umid_avg=Avg("umidade"),
                pm1_0_avg=Avg("pm1_0"),
                pm2_5_avg=Avg("pm2_5"),
                pm10_avg=Avg("pm10"),
            )
            .order_by("dia")
        )
        for grupo in agrupados:
            label = grupo["dia"].strftime("%d/%m")
            if periodo == "semana":
                dados_temperatura["semana"]["labels"].append(label)
                dados_temperatura["semana"]["data"].append(
                    round(grupo["temp_avg"], 1)
                    if grupo["temp_avg"] is not None
                    else None
                )
                dados_umidade["semana"]["labels"].append(label)
                dados_umidade["semana"]["data"].append(
                    round(grupo["umid_avg"], 1)
                    if grupo["umid_avg"] is not None
                    else None
                )
                dados_particulas["semana"]["labels"].append(label)
                dados_particulas["semana"]["data"]["pm1_0"].append(
                    round(grupo["pm1_0_avg"], 1)
                    if grupo["pm1_0_avg"] is not None
                    else None
                )
                dados_particulas["semana"]["data"]["pm2_5"].append(
                    round(grupo["pm2_5_avg"], 1)
                    if grupo["pm2_5_avg"] is not None
                    else None
                )
                dados_particulas["semana"]["data"]["pm10"].append(
                    round(grupo["pm10_avg"], 1)
                    if grupo["pm10_avg"] is not None
                    else None
                )
            else:
                dados_temperatura["mes"]["labels"].append(label)
                dados_temperatura["mes"]["data"].append(
                    round(grupo["temp_avg"], 1)
                    if grupo["temp_avg"] is not None
                    else None
                )
                dados_umidade["mes"]["labels"].append(label)
                dados_umidade["mes"]["data"].append(
                    round(grupo["umid_avg"], 1)
                    if grupo["umid_avg"] is not None
                    else None
                )
                dados_particulas["mes"]["labels"].append(label)
                dados_particulas["mes"]["data"]["pm1_0"].append(
                    round(grupo["pm1_0_avg"], 1)
                    if grupo["pm1_0_avg"] is not None
                    else None
                )
                dados_particulas["mes"]["data"]["pm2_5"].append(
                    round(grupo["pm2_5_avg"], 1)
                    if grupo["pm2_5_avg"] is not None
                    else None
                )
                dados_particulas["mes"]["data"]["pm10"].append(
                    round(grupo["pm10_avg"], 1)
                    if grupo["pm10_avg"] is not None
                    else None
                )

    context["dados_temperatura"] = json.dumps(dados_temperatura)
    context["dados_umidade"] = json.dumps(dados_umidade)
    context["dados_particulas"] = json.dumps(dados_particulas)

    return render(request, "estatisticas.html", context)


@login_required(login_url="login")
def sobre(request):
    return render(request, "sobre.html")


@login_required(login_url="login")
def ajuda(request):
    return render(request, "ajuda.html")
