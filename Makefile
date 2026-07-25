.PHONY: setup sprint1 lint format typecheck test coverage clean

setup:
	python -m venv .venv
	. .venv/bin/activate && python -m pip install -U pip

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
	pytest --cov=packages --cov-report=term --cov-report=html

clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -f .coverage
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
