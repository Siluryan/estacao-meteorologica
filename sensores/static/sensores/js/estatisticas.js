/** Statistics Page JavaScript */

(function() {
    'use strict';

    let temperatureChart = null;
    let humidityChart = null;
    let airParticlesChart = null;

    function showTab(tabName) {
        const tabContents = document.getElementsByClassName("tab-content");
        for (let i = 0; i < tabContents.length; i++) {
            tabContents[i].classList.remove("active");
            tabContents[i].style.display = "none";
        }
        const tabButtons = document.getElementsByClassName("tab-button");
        for (let i = 0; i < tabButtons.length; i++) {
            tabButtons[i].classList.remove("active");
        }
        document.getElementById(tabName).classList.add("active");
        document.getElementById(tabName).style.display = "block";
        document.getElementById(tabName + "-btn").classList.add("active");
        localStorage.setItem('activeTab', tabName);
        
        if (tabName === 'graficos') {
            setTimeout(function() {
                initCharts();
            }, 100);
        }
    }

    function filtrarDados() {
        const periodo = document.getElementById('periodo').value;
        window.location.href = `/estatisticas/?periodo=${periodo}`;
    }

    function initCharts() {
        try {
            if (typeof Chart === 'undefined') {
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
                script.onload = function() {
                    initCharts();
                };
                document.head.appendChild(script);
                return;
            }

            const periodo = document.getElementById('periodo').value;
            if (!window.dadosTemperatura || !window.dadosUmidade || !window.dadosParticulas) return;
            if (!window.dadosTemperatura[periodo] || !window.dadosUmidade[periodo] || !window.dadosParticulas[periodo]) return;

            let xAxisConfig = {
                display: true,
                ticks: {
                    font: { size: 7 },
                    maxRotation: 0,
                    autoSkip: true
                },
                grid: { display: false }
            };
            
            if (periodo === 'hoje') {
                xAxisConfig.ticks.maxTicksLimit = 8;
            } else if (periodo === 'semana') {
                xAxisConfig.ticks.maxTicksLimit = 7;
            } else {
                xAxisConfig.ticks.maxTicksLimit = 4;
            }

            const temperatureCtx = document.getElementById('temperatureChart');
            const humidityCtx = document.getElementById('humidityChart');
            const airParticlesCtx = document.getElementById('airParticlesChart');
            
            if (!temperatureCtx || !humidityCtx || !airParticlesCtx) return;

            if (temperatureChart) temperatureChart.destroy();
            if (humidityChart) humidityChart.destroy();
            if (airParticlesChart) airParticlesChart.destroy();

            temperatureChart = new Chart(temperatureCtx, {
                type: 'line',
                data: {
                    labels: window.dadosTemperatura[periodo].labels,
                    datasets: [{
                        label: 'Temperatura (°C)',
                        data: window.dadosTemperatura[periodo].data,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1,
                        fill: true,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true, mode: 'index', intersect: false }
                    },
                    scales: {
                        y: {
                            display: true,
                            title: { display: true, text: '°C', font: { size: 8 } },
                            ticks: { font: { size: 7 }, maxTicksLimit: 3 },
                            grid: { display: false }
                        },
                        x: xAxisConfig
                    }
                }
            });

            humidityChart = new Chart(humidityCtx, {
                type: 'line',
                data: {
                    labels: window.dadosUmidade[periodo].labels,
                    datasets: [{
                        label: 'Umidade (%)',
                        data: window.dadosUmidade[periodo].data,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1,
                        fill: true,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true, mode: 'index', intersect: false }
                    },
                    scales: {
                        y: {
                            display: true,
                            title: { display: true, text: '%', font: { size: 8 } },
                            ticks: { font: { size: 7 }, maxTicksLimit: 3 },
                            grid: { display: false }
                        },
                        x: xAxisConfig
                    }
                }
            });

            airParticlesChart = new Chart(airParticlesCtx, {
                type: 'line',
                data: {
                    labels: window.dadosParticulas[periodo].labels,
                    datasets: [
                        {
                            label: 'PM1.0',
                            data: window.dadosParticulas[periodo].data.pm1_0,
                            borderColor: 'rgb(201, 203, 207)',
                            backgroundColor: 'rgba(201, 203, 207, 0.2)',
                            tension: 0.1,
                            borderWidth: 1
                        },
                        {
                            label: 'PM2.5',
                            data: window.dadosParticulas[periodo].data.pm2_5,
                            borderColor: 'rgb(255, 99, 71)',
                            backgroundColor: 'rgba(255, 99, 71, 0.2)',
                            tension: 0.1,
                            borderWidth: 1
                        },
                        {
                            label: 'PM10',
                            data: window.dadosParticulas[periodo].data.pm10,
                            borderColor: 'rgb(128, 0, 128)',
                            backgroundColor: 'rgba(128, 0, 128, 0.2)',
                            tension: 0.1,
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { boxWidth: 8, font: { size: 7 } }
                        },
                        tooltip: { enabled: true, mode: 'index', intersect: false }
                    },
                    scales: {
                        y: {
                            display: true,
                            title: { display: true, text: 'µg/m³', font: { size: 8 } },
                            ticks: { font: { size: 7 }, maxTicksLimit: 3 },
                            grid: { display: false }
                        },
                        x: xAxisConfig
                    }
                }
            });
        } catch (error) {
            console.error("Erro ao inicializar gráficos:", error);
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('tabelas-btn').addEventListener('click', function() {
            showTab('tabelas');
        });
        
        document.getElementById('graficos-btn').addEventListener('click', function() {
            showTab('graficos');
        });
        
        const savedTab = localStorage.getItem('activeTab') || 'tabelas';
        showTab(savedTab);
        
        const urlParams = new URLSearchParams(window.location.search);
        const periodoParam = urlParams.get('periodo');
        if (periodoParam) {
            document.getElementById('periodo').value = periodoParam;
        }

        window.filtrarDados = filtrarDados;
    });
})();

