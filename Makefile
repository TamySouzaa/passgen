.PHONY: install run test format help

install:
	pip install -r requirements.txt

run:
	python main.py

test:
	python -m pytest tests/ -v --cov=.

format:
	black . && isort .

help:
	python -c "print('Comandos disponíveis:')"
	python -c "print('  pip install -r requirements.txt  - Instala as dependencias')"
	python -c "print('  python main.py                   - Executa o gerador de senhas')"
	python -c "print('  python -m pytest tests/ -v       - Executa os testes')"
	python -c "print('  black . && isort .               - Formata o codigo')"