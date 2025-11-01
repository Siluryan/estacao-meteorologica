/** Map Management Module */

const MapManager = {
    map: null,
    marker: null,

    init() {
        try {
            const mapElement = document.getElementById('map');
            if (!mapElement) return;

            this.map = L.map('map').setView([-23.550520, -46.633308], 13);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(this.map);
            
            console.log('Mapa inicializado com sucesso');
        } catch (e) {
            console.error('Erro ao inicializar o mapa:', e);
        }
    },

    update(lat, lon, local) {
        if (!this.map) {
            console.error('Mapa não inicializado');
            return;
        }

        const coordenadasElement = document.getElementById('coordenadas');
        const localElement = document.getElementById('local');

        if (coordenadasElement) {
            coordenadasElement.textContent = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
        }

        if (localElement) {
            localElement.textContent = local || 'Local desconhecido';
        }

        this.map.setView([lat, lon], 13);

        if (this.marker) {
            this.marker.setLatLng([lat, lon]);
        } else {
            this.marker = L.marker([lat, lon]).addTo(this.map);
        }
    }
};

