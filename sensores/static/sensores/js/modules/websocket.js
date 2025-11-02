/** WebSocket Management Module */

const WebSocketManager = {
    ws: null,
    reconnectDelay: 5000,

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket já está conectado.');
            this.updateStatus('connected');
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/`;

        try {
            console.log(`Tentando conectar ao WebSocket em ${wsUrl}`);
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('Conexão WebSocket estabelecida com sucesso!');
                this.updateStatus('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Dados recebidos:', data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('Erro ao processar mensagem do WebSocket:', e);
                }
            };

            this.ws.onclose = (e) => {
                console.log(`WebSocket desconectado (código: ${e.code}, razão: ${e.reason}). Tentando reconectar em ${this.reconnectDelay/1000} segundos...`);
                this.updateStatus('disconnected');
                setTimeout(() => this.connect(), this.reconnectDelay);
            };

            this.ws.onerror = (err) => {
                console.error('Erro no WebSocket:', err);
                this.updateStatus('disconnected');
            };
        } catch (e) {
            console.error('Erro ao criar conexão WebSocket:', e);
            this.updateStatus('disconnected');
            setTimeout(() => this.connect(), this.reconnectDelay);
        }
    },

    handleMessage(data) {
        if (data.temperatura !== undefined) {
            document.getElementById('temperatura').textContent = data.temperatura;
            ChartsManager.updateChart('temperatura', data.temperatura);
        }

        if (data.umidade !== undefined) {
            document.getElementById('umidade').textContent = data.umidade;
            ChartsManager.updateChart('umidade', data.umidade);
        }

        if (data.luminosidade !== undefined) {
            document.getElementById('luminosidade').textContent = data.luminosidade;
            ChartsManager.updateChart('luminosidade', data.luminosidade);
            IndicatorsManager.updateLuminosidadeIcon(data.luminosidade);
        }

        if (data.data_hora) {
            const element = document.getElementById('data_hora');
            if (element) {
                element.textContent = Utils.formatarDataHora(data.data_hora);
            }
        }

        if (data.latitude && data.longitude) {
            MapManager.update(data.latitude, data.longitude, data.localizacao);
        }

        if (data.chuva !== undefined) {
            IndicatorsManager.updateChuva(data.chuva);
        }

        if (data.corrente !== undefined) {
            const element = document.getElementById('corrente');
            if (element) element.textContent = Math.round(data.corrente);
            ChartsManager.updateChart('corrente', data.corrente);
            IndicatorsManager.evaluateCorrente(data.corrente);
        }

        if (data.gas_detectado !== undefined) {
            IndicatorsManager.updateGas(data.gas_detectado);
        }

        if (data.pm1_0 !== undefined) {
            const element = document.getElementById('pm1_0');
            if (element) element.textContent = data.pm1_0;
            ChartsManager.updateChart('pm1_0', data.pm1_0);
            IndicatorsManager.evaluatePM1(data.pm1_0);
        }

        if (data.pm2_5 !== undefined) {
            const element = document.getElementById('pm2_5');
            if (element) element.textContent = data.pm2_5;
            ChartsManager.updateChart('pm2_5', data.pm2_5);
            IndicatorsManager.evaluatePM25(data.pm2_5);
        }

        if (data.pm10 !== undefined) {
            const element = document.getElementById('pm10');
            if (element) element.textContent = data.pm10;
            ChartsManager.updateChart('pm10', data.pm10);
            IndicatorsManager.evaluatePM10(data.pm10);
        }

        if (data.vento_kmh !== undefined) {
            const kmhElement = document.getElementById('vento_kmh');
            const msElement = document.getElementById('vento_ms');
            if (kmhElement) kmhElement.textContent = data.vento_kmh.toFixed(1);
            if (msElement) {
                msElement.textContent = data.vento_ms 
                    ? data.vento_ms.toFixed(2) + ' m/s' 
                    : '--';
            }
            ChartsManager.updateChart('vento', data.vento_kmh);
        }

        if (data.umidade_solo_pct !== undefined) {
            const element = document.getElementById('umidade_solo');
            if (element) element.textContent = data.umidade_solo_pct.toFixed(1);
            ChartsManager.updateChart('solo', data.umidade_solo_pct);
        }

        if (data.pressao_hpa !== undefined) {
            const element = document.getElementById('pressao');
            if (element) element.textContent = data.pressao_hpa.toFixed(1);
            ChartsManager.updateChart('pressao', data.pressao_hpa);
        }

        if (data.altitude_m !== undefined) {
            const element = document.getElementById('altitude');
            if (element) element.textContent = data.altitude_m.toFixed(1);
            ChartsManager.updateChart('altitude', data.altitude_m);
        }

        if (data.temperatura_bmp !== undefined) {
            const element = document.getElementById('temperatura_bmp');
            if (element) element.textContent = data.temperatura_bmp.toFixed(1);
            ChartsManager.updateChart('temperatura_bmp', data.temperatura_bmp);
        }
    },

    updateStatus(status) {
        const statusIndicator = document.getElementById('ws_status');
        if (!statusIndicator) return;

        if (status === 'connected') {
            statusIndicator.className = 'badge bg-success';
            statusIndicator.textContent = 'Conectado';
        } else {
            statusIndicator.className = 'badge bg-danger';
            statusIndicator.textContent = 'Desconectado';
        }
    },

    test() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket está conectado. Tudo bem!');
            alert('WebSocket conectado com sucesso!');
        } else {
            console.error('WebSocket não está conectado!');
            alert('WebSocket não está conectado!');
            this.connect();
        }
    }
};

