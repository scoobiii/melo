.DEFAULT_GOAL := help

.PHONY: \
	help \
	setup \
	deps \
	install \
	check \
	sprint1 \
	lint \
	format \
	typecheck \
	test \
	coverage \
	analyze-mix \
	catalog \
	docs \
	all \
	clean \
	distclean

help:
	@echo ""
	@echo "=========================================="
	@echo " MELO — Music Analysis Factory"
	@echo "=========================================="
	@echo ""
	@echo "Instalação"
	@echo "  make setup                 Cria ambiente virtual (.venv)"
	@echo "  make deps                  Instala dependências"
	@echo "  make install               Setup + deps + check"
	@echo ""
	@echo "Verificação"
	@echo "  make check                 Verifica ambiente"
	@echo ""
	@echo "Desenvolvimento"
	@echo "  make sprint1               Executa Sprint 1"
	@echo "  make lint                  Ruff"
	@echo "  make format                Black"
	@echo "  make typecheck             MyPy"
	@echo "  make test                  Pytest"
	@echo "  make coverage              Cobertura"
	@echo ""
	@echo "Análise"
	@echo "  make analyze-mix WAV=arquivo.wav"
	@echo "  make catalog"
	@echo "  make docs"
	@echo ""
	@echo "Pipeline"
	@echo "  make all"
	@echo ""
	@echo "Limpeza"
	@echo "  make clean"
	@echo "  make distclean"
	@echo ""

setup:
	python3 -m venv .venv

deps:
	. .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements/dev.txt

install: setup deps check

check:
	@echo "== Ambiente =="
	@python3 --version
	@which ffmpeg >/dev/null && ffmpeg -version | head -1 || echo "FFmpeg: NÃO encontrado"
	@which sqlite3 >/dev/null && sqlite3 --version || echo "SQLite3: NÃO encontrado"
	@echo "OK"

sprint1:
	bash scripts/sprint1.sh

lint:
	ruff check .

format:
	black .

typecheck:
	mypy packages

test:
	pytest

coverage:
	pytest --cov=packages \
	       --cov-report=term \
	       --cov-report=html

analyze-mix:
	PYTHONPATH=. python3 scripts/full_mix_analysis.py \
		$(WAV) \
		--out output/mix_analise.json \
		--modelo tiny \
		--idioma es

catalog:
	bash scripts/validate-latest-catalog.sh

docs:
	PYTHONPATH=. python3 scripts/generate_docs.py

all:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
	$(MAKE) coverage

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -f .coverage
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

distclean: clean
	rm -rf .venv
	rm -rf outputs
	rm -rf output
	rm -rf data/*.sqlite
	rm -rf data/*.db
	rm -f server.log
