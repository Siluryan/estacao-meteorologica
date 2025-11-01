/** Charts Management Module */

const ChartsManager = {
    charts: {},
    dataArrays: {},
    chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        elements: { point: { radius: 0 }, line: { tension: 0.3 } },
        scales: {
            x: { display: false },
            y: { display: false, beginAtZero: false }
        },
        animation: false
    },

    chartConfigs: {
        temperatura: { id: 'tempChart', color: '#2e7d32', dataArray: 'tempData' },
        umidade: { id: 'umidChart', color: '#388e3c', dataArray: 'umidData' },
        luminosidade: { id: 'luxChart', color: '#4CAF50', dataArray: 'luxData' },
        corrente: { id: 'correnteChart', color: '#66BB6A', dataArray: 'correnteData' },
        pm1_0: { id: 'pm1Chart', color: '#607D8B', dataArray: 'pm1Data' },
        pm2_5: { id: 'pm25Chart', color: '#607D8B', dataArray: 'pm25Data' },
        pm10: { id: 'pm10Chart', color: '#607D8B', dataArray: 'pm10Data' },
        vento: { id: 'ventoChart', color: '#4CAF50', dataArray: 'ventoData' },
        solo: { id: 'soloChart', color: '#8BC34A', dataArray: 'soloData' },
        pressao: { id: 'pressaoChart', color: '#66BB6A', dataArray: 'pressaoData' },
        altitude: { id: 'altitudeChart', color: '#81C784', dataArray: 'altitudeData' },
        temperatura_bmp: { id: 'tempBmpChart', color: '#AED581', dataArray: 'tempBmpData' }
    },

    init() {
        this.initializeDataArrays();
        this.createAllCharts();
    },

    initializeDataArrays() {
        const initialData = [0, 0, 0, 0, 0];
        const defaultValues = {
            tempData: [25, 25, 25, 25, 25],
            umidData: [50, 50, 50, 50, 50],
            luxData: [500, 500, 500, 500, 500],
            correnteData: initialData,
            pm1Data: initialData,
            pm25Data: initialData,
            pm10Data: initialData,
            ventoData: initialData,
            soloData: initialData,
            pressaoData: initialData,
            altitudeData: initialData,
            tempBmpData: initialData
        };

        Object.keys(defaultValues).forEach(key => {
            this.dataArrays[key] = [...defaultValues[key]];
        });
    },

    createAllCharts() {
        Object.keys(this.chartConfigs).forEach(key => {
            const config = this.chartConfigs[key];
            const element = document.getElementById(config.id);
            
            if (element) {
                try {
                    this.charts[key] = new Chart(element, {
                        type: 'line',
                        data: {
                            labels: ['', '', '', '', ''],
                            datasets: [{
                                data: this.dataArrays[config.dataArray],
                                borderColor: config.color,
                                borderWidth: 2,
                                fill: false
                            }]
                        },
                        options: this.chartOptions
                    });
                } catch (error) {
                    console.error(`Erro ao criar gráfico ${key}:`, error);
                }
            }
        });
    },

    updateChart(sensorKey, value) {
        const config = this.chartConfigs[sensorKey];
        if (!config || !this.charts[sensorKey]) return;

        const dataArray = this.dataArrays[config.dataArray];
        dataArray.push(value);
        dataArray.shift();
        this.charts[sensorKey].update();
    }
};

