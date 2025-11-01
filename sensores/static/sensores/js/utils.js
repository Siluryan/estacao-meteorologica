/** Utility Functions */

const Utils = {
    /**
     * Formata data e hora para exibição em português
     * @param {string} dataHora - String de data/hora ISO
     * @returns {string} Data formatada
     */
    formatarDataHora(dataHora) {
        try {
            const data = new Date(dataHora);
            return data.toLocaleString('pt-BR');
        } catch (e) {
            console.error('Erro ao formatar data:', e);
            return dataHora;
        }
    },

    /**
     * Arredonda número para n casas decimais
     * @param {number} valor - Valor a arredondar
     * @param {number} decimais - Número de casas decimais
     * @returns {number} Valor arredondado
     */
    arredondar(valor, decimais = 1) {
        return parseFloat(valor.toFixed(decimais));
    }
};

