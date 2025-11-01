/** Indicators Management Module */

const IndicatorsManager = {
    updateChuva(chuva) {
        const indicator = document.getElementById('chuva_indicator');
        const texto = document.getElementById('chuva');
        
        if (!indicator || !texto) return;

        if (chuva) {
            indicator.classList.add('active');
            indicator.style.backgroundColor = '#2196F3';
            indicator.style.boxShadow = '0 0 10px #2196F3';
            texto.textContent = 'Detectada';
        } else {
            indicator.classList.remove('active');
            indicator.style.backgroundColor = '#ccc';
            indicator.style.boxShadow = 'none';
            texto.textContent = 'Não detectada';
        }
    },

    updateGas(detectado) {
        const indicator = document.getElementById('gas_indicator');
        const texto = document.getElementById('gas_detectado');
        
        if (!indicator || !texto) return;

        if (detectado) {
            indicator.classList.add('active');
            indicator.style.backgroundColor = '#ff4d4d';
            indicator.style.boxShadow = '0 0 10px #ff4d4d';
            texto.textContent = 'ALERTA';
        } else {
            indicator.classList.remove('active');
            indicator.style.backgroundColor = '#2e7d32';
            indicator.style.boxShadow = 'none';
            texto.textContent = 'Normal';
        }
    },

    updateLuminosidadeIcon(luminosidade) {
        const iconeElement = document.getElementById('lux_icon');
        if (!iconeElement || luminosidade <= 0) return;

        let iconHtml = '';
        if (luminosidade < 200) {
            iconHtml = '<i class="fas fa-moon text-primary"></i>';
        } else if (luminosidade < 800) {
            iconHtml = '<i class="fas fa-cloud-sun text-warning"></i>';
        } else {
            iconHtml = '<i class="fas fa-sun text-warning"></i>';
        }
        iconeElement.innerHTML = iconHtml;
    },

    evaluateCorrente(corrente) {
        const statusElement = document.getElementById('corrente_status');
        if (!statusElement) return;

        const thresholds = [
            { max: Infinity, text: 'ALERTA: Consumo muito alto!', color: '#F44336' },
            { max: 4000, text: 'Consumo elevado', color: '#FF9800' },
            { max: 2500, text: 'Consumo moderado', color: '#FFEB3B' },
            { max: 1500, text: 'Consumo normal', color: '#4CAF50' }
        ];

        const threshold = thresholds.find(t => corrente <= t.max);
        if (threshold) {
            statusElement.textContent = threshold.text;
            statusElement.style.color = threshold.color;
        }
    },

    evaluatePM1(valor) {
        this.evaluatePM('pm1', valor, [
            { max: 10, level: 'BOM', color: '#4CAF50', text: 'Nível seguro de partículas ultrafinas' },
            { max: 25, level: 'MODERADO', color: '#FFEB3B', text: 'Nível aceitável de partículas ultrafinas' },
            { max: 50, level: 'RUIM', color: '#FF9800', text: 'Nível elevado de partículas ultrafinas' },
            { max: 75, level: 'MUITO RUIM', color: '#F44336', text: 'Nível perigoso de partículas ultrafinas' },
            { max: Infinity, level: 'PÉSSIMO', color: '#9C27B0', text: 'Nível extremamente perigoso' }
        ]);
    },

    evaluatePM25(valor) {
        this.evaluatePM('pm25', valor, [
            { max: 12, level: 'BOM', color: '#4CAF50', text: 'Qualidade do ar boa' },
            { max: 35.4, level: 'MODERADO', color: '#FFEB3B', text: 'Qualidade do ar aceitável' },
            { max: 55.4, level: 'RUIM', color: '#FF9800', text: 'Insalubre para grupos sensíveis' },
            { max: 150.4, level: 'MUITO RUIM', color: '#F44336', text: 'Insalubre para todos' },
            { max: Infinity, level: 'PÉSSIMO', color: '#9C27B0', text: 'Perigoso para a saúde' }
        ]);
    },

    evaluatePM10(valor) {
        this.evaluatePM('pm10', valor, [
            { max: 54, level: 'BOM', color: '#4CAF50', text: 'Qualidade do ar boa' },
            { max: 154, level: 'MODERADO', color: '#FFEB3B', text: 'Qualidade do ar aceitável' },
            { max: 254, level: 'RUIM', color: '#FF9800', text: 'Insalubre para grupos sensíveis' },
            { max: 354, level: 'MUITO RUIM', color: '#F44336', text: 'Insalubre para todos' },
            { max: Infinity, level: 'PÉSSIMO', color: '#9C27B0', text: 'Perigoso para a saúde' }
        ]);
    },

    evaluatePM(pmType, valor, thresholds) {
        const qualityElement = document.getElementById(`${pmType}_quality`);
        const statusElement = document.getElementById(`${pmType}_status`);
        
        if (!qualityElement || !statusElement) return;

        const threshold = thresholds.find(t => valor <= t.max);
        if (threshold) {
            qualityElement.textContent = threshold.level;
            qualityElement.style.backgroundColor = threshold.color;
            statusElement.textContent = threshold.text;
        }
    }
};

