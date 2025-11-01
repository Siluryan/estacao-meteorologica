/** Dashboard Main Module */

(function() {
    'use strict';

    function init() {
        console.log('Página carregada, iniciando configuração...');

        ChartsManager.init();
        MapManager.init();
        WebSocketManager.connect();

        const luxIcon = document.getElementById('lux_icon');
        if (luxIcon) {
            luxIcon.innerHTML = '<i class="fas fa-sun text-warning"></i>';
        }

        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible' && 
                (!WebSocketManager.ws || WebSocketManager.ws.readyState !== WebSocket.OPEN)) {
                console.log('Página visível novamente, tentando reconectar WebSocket...');
                WebSocketManager.connect();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

