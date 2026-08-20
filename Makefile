# markdown-tools — Development Makefile
# Stack: Python 3.11+ / uv
# Utilities: md2pdf (markdown → PDF conversion)

.DEFAULT_GOAL := help
.PHONY: help setup md2pdf lint test clean

# Homebrew library path (required for WeasyPrint to find pango/cairo on macOS)
export DYLD_FALLBACK_LIBRARY_PATH := $(shell brew --prefix)/lib

# Defaults
SOURCE ?= .
OUTPUT ?= ./output
DEPTH ?=

help: ## Show available commands
	@echo "Usage: make [target]"
	@echo ""
	@echo "  Utilities:"
	@echo "  md2pdf         Convert markdown to PDF (SOURCE, OUTPUT, DEPTH)"
	@echo ""
	@echo "  Development:"
	@echo "  setup          Install dependencies"
	@echo "  lint           Run linter"
	@echo "  test           Run test suite"
	@echo "  clean          Remove output files"

# ─── Utilities ────────────────────────────────────────────────────────────────

md2pdf: ## Convert markdown → PDF
	@uv run md2pdf $(SOURCE) --output $(OUTPUT) $(if $(DEPTH),--depth $(DEPTH),)

# ─── Development Lifecycle ────────────────────────────────────────────────────

setup: ## Install all dependencies
	@echo "📦 Installing dependencies..."
	@if ! pkg-config --exists pango 2>/dev/null; then \
		echo "📎 Installing pango (required by WeasyPrint)..."; \
		/opt/homebrew/bin/brew install pango; \
	else \
		echo "✓ pango already installed"; \
	fi
	@uv sync
	@echo "✅ Setup complete."

lint: ## Run ruff linter
	@echo "🔍 Linting..."
	@uv run ruff check src/ tests/
	@echo "✅ Lint passed."

test: ## Run test suite
	@echo "🧪 Running tests..."
	@uv run pytest tests/
	@echo "✅ Tests passed."

clean: ## Remove output directory
	@echo "🧹 Cleaning..."
	@rm -rf output/
	@echo "✅ Clean."
