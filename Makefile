.PHONY: all format lint type-check test dev clean install-dev help install-docs docs serve-docs

# Python execution through Poetry
PYTHON = poetry run

# Default target
all: format lint type-check test

# Format code with ruff and isort
format:
	@echo "🎨 Formatting code..."
	$(PYTHON) ruff format src/palo_alto_mcp tests
	$(PYTHON) isort src/palo_alto_mcp tests

# Run linting checks
lint:
	@echo "🔍 Running linters..."
	$(PYTHON) ruff check src/palo_alto_mcp tests
	$(PYTHON) flake8 src/palo_alto_mcp tests

# Run type checking
type-check:
	@echo "📝 Running type checker..."
	$(PYTHON) mypy src/palo_alto_mcp tests

# Run tests with pytest
test:
	@echo "🧪 Running tests..."
	$(PYTHON) pytest -v --cov=palo_alto_mcp --cov-report=term-missing tests/

# Run tests and watch for changes
test-watch:
	@echo "👀 Running tests in watch mode..."
	$(PYTHON) pytest-watch -- -v --cov=palo_alto_mcp --cov-report=term-missing tests/

# Run development server
dev:
	@echo "🚀 Starting development server..."
	$(PYTHON) mcp dev

# Clean up cache and build artifacts
clean:
	@echo "🧹 Cleaning up..."
	rm -rf .pytest_cache .coverage .mypy_cache .ruff_cache htmlcov
	rm -rf dist build *.egg-info site/
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Install development dependencies
install-dev:
	@echo "📦 Installing development dependencies..."
	poetry install --with dev

# Documentation targets
install-docs:
	@echo "📚 Installing documentation dependencies..."
	pip install mkdocs-material \
		mkdocs-mermaid2-plugin \
		mkdocstrings \
		mkdocstrings-python \
		mkdocs-minify-plugin \
		mkdocs-git-revision-date-localized-plugin

docs:
	@echo "📖 Building documentation..."
	mkdocs build

serve-docs:
	@echo "🌐 Serving documentation locally..."
	mkdocs serve

# Help target
help:
	@echo "Available targets:"
	@echo "  make          : Run all checks (format, lint, type-check, test)"
	@echo "  make format   : Format code with ruff and isort"
	@echo "  make lint     : Run linting checks with ruff and flake8"
	@echo "  make type-check: Run type checking with mypy"
	@echo "  make test     : Run tests with pytest"
	@echo "  make test-watch: Run tests in watch mode"
	@echo "  make dev      : Start development server"
	@echo "  make clean    : Clean up cache and build artifacts"
	@echo "  make install-dev: Install development dependencies"
	@echo "  make install-docs: Install MkDocs and required plugins"
	@echo "  make docs    : Build the documentation site"
	@echo "  make serve-docs: Serve the documentation site locally"

# Default target
.DEFAULT_GOAL := help 