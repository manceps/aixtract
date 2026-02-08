.PHONY: install dev test lint format build publish-test publish clean

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Install production dependencies
install:
	$(PIP) install -e .

# Install development dependencies
dev:
	$(PIP) install -e ".[all,dev]"

# Run tests
test:
	$(VENV)/bin/pytest tests/ -v --cov=aixtract --cov-report=term-missing

# Run tests in parallel
test-parallel:
	$(VENV)/bin/pytest tests/ -v -n auto

# Run linting
lint:
	$(VENV)/bin/ruff check src/ tests/

# Format code
format:
	$(VENV)/bin/ruff format src/ tests/
	$(VENV)/bin/ruff check --fix src/ tests/

# Build distribution
build: clean
	$(PYTHON) -m build

# Upload to TestPyPI
publish-test: build
	$(VENV)/bin/twine upload --repository testpypi dist/*

# Upload to PyPI
publish: build
	$(VENV)/bin/twine upload dist/*

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
