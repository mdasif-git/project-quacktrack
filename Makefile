.PHONY: help install install-dev lint format test pre-commit run clean

help:
	@echo "Available commands:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install dev dependencies"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code with black"
	@echo "  make test             Run tests with coverage"
	@echo "  make pre-commit       Setup pre-commit hooks"
	@echo "  make run              Run the main script"
	@echo "  make clean            Remove build artifacts"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

lint:
	black --check src/ tests/
	flake8 src/ tests/

format:
	black src/ tests/
	isort src/ tests/

test:
	pytest tests/ -v

pre-commit:
	pre-commit install
	pre-commit run --all-files

run:
	python -m quacktrack.main

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage
