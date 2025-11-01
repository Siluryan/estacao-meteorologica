.PHONY: format format-check install-black help

help:
	@echo "Comandos disponíveis:"
	@echo "  make format        - Formata todo o código Python com Black"
	@echo "  make format-check  - Verifica se o código está formatado (sem alterar)"
	@echo "  make install-black - Instala o Black"
	@echo "  make help          - Mostra esta ajuda"

install-black:
	pip install black==24.10.0

format:
	black .

format-check:
	black --check .
