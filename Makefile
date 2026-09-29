# markdown-tools — Development Makefile
# Stack: Python 3.11+ / uv
# Utilities: md2pdf (markdown → PDF conversion)

.DEFAULT_GOAL := help
.PHONY: help setup install install-system uninstall uninstall-system md2pdf lint test clean

# Homebrew library path (required for WeasyPrint to find pango/cairo on macOS)
export DYLD_FALLBACK_LIBRARY_PATH := $(shell brew --prefix)/lib

# Defaults
SOURCE ?= .
OUTPUT ?= ./output
DEPTH ?=
PREFIX ?= /usr/local

help: ## Show available commands
	@echo "Usage: make [target]"
	@echo ""
	@echo "  Install (current user):"
	@echo "  install        Install md2pdf for current user (~/.local/bin)"
	@echo "  uninstall      Remove current-user installation"
	@echo ""
	@echo "  Install (system-wide / shared prefix):"
	@echo "  install-system   Install md2pdf to PREFIX (default: $(PREFIX))"
	@echo "  uninstall-system Remove PREFIX installation"
	@echo ""
	@echo "  Utilities:"
	@echo "  md2pdf         Convert markdown to PDF (SOURCE, OUTPUT, DEPTH)"
	@echo ""
	@echo "  Development:"
	@echo "  setup          Install dependencies (for local dev)"
	@echo "  lint           Run linter"
	@echo "  test           Run test suite"
	@echo "  clean          Remove output files"
	@echo ""
	@echo "  Variables:"
	@echo "  PREFIX         System install location (default: /usr/local)"

# ─── Install / Uninstall ──────────────────────────────────────────────────────

install: ## Install md2pdf for current user (~/.local/bin)
	@echo "📦 Installing md2pdf for current user..."
	@if ! pkg-config --exists pango 2>/dev/null; then \
		echo "📎 Installing pango (required by WeasyPrint)..."; \
		/opt/homebrew/bin/brew install pango; \
	fi
	@# --reinstall --no-cache: the version stays 0.1.0 between edits, so a plain
	@# `uv tool install` would reuse a stale cached wheel and install OLD code.
	@# Always build from current source.
	@uv tool install --force --reinstall --no-cache .
	@TOOL_BIN="$$HOME/.local/share/uv/tools/markdown-tools/bin/md2pdf"; \
	BREW_LIB="$$(brew --prefix 2>/dev/null)/lib"; \
	rm -f "$$HOME/.local/bin/md2pdf"; \
	printf '#!/bin/sh\nexport DYLD_FALLBACK_LIBRARY_PATH="%s$${DYLD_FALLBACK_LIBRARY_PATH:+:$$DYLD_FALLBACK_LIBRARY_PATH}"\nexec "%s" "$$@"\n' "$$BREW_LIB" "$$TOOL_BIN" > "$$HOME/.local/bin/md2pdf"; \
	chmod +x "$$HOME/.local/bin/md2pdf"
	@echo ""
	@echo "✅ md2pdf installed. You can now run it from any terminal:"
	@echo "   md2pdf <file-or-dir> --output ./pdfs"
	@echo ""
	@echo "ℹ️  If 'md2pdf' is not found, ensure ~/.local/bin is on your PATH:"
	@echo "   export PATH=\"\$$HOME/.local/bin:\$$PATH\""

uninstall: ## Remove current-user installation
	@echo "🗑️  Uninstalling md2pdf..."
	@uv tool uninstall markdown-tools
	@echo "✅ md2pdf removed."

install-system: ## Install md2pdf system-wide (may require sudo depending on PREFIX)
	@if [ ! -w "$(PREFIX)" ] && [ ! -w "$$(dirname $(PREFIX))" ]; then \
		echo "❌ Cannot write to $(PREFIX). Either:"; \
		echo "   • Run with sudo:  sudo make install-system"; \
		echo "   • Use a prefix you own:  make install-system PREFIX=~/tools"; \
		echo "   • Create the directory:  sudo mkdir -p $(PREFIX) && sudo chown $$USER $(PREFIX)"; \
		exit 1; \
	fi
	@echo "📦 Installing md2pdf to $(PREFIX)/bin..."
	@if ! pkg-config --exists pango 2>/dev/null; then \
		echo "📎 pango not found. Install it first:"; \
		echo "   brew install pango        (macOS)"; \
		echo "   apt install libpango1.0-dev  (Debian/Ubuntu)"; \
		exit 1; \
	fi
	@mkdir -p $(PREFIX)/share/md2pdf $(PREFIX)/bin
	@uv build --wheel --out-dir $(PREFIX)/share/md2pdf
	@uv venv --python 3.11 $(PREFIX)/share/md2pdf/.venv
	@uv pip install --python $(PREFIX)/share/md2pdf/.venv/bin/python $(PREFIX)/share/md2pdf/*.whl
	@BREW_LIB="$$(brew --prefix 2>/dev/null)/lib"; \
	REAL_BIN="$(PREFIX)/share/md2pdf/.venv/bin/md2pdf"; \
	printf '#!/bin/sh\nexport DYLD_FALLBACK_LIBRARY_PATH="%s$${DYLD_FALLBACK_LIBRARY_PATH:+:$$DYLD_FALLBACK_LIBRARY_PATH}"\nexec "%s" "$$@"\n' "$$BREW_LIB" "$$REAL_BIN" > $(PREFIX)/bin/md2pdf; \
	chmod +x $(PREFIX)/bin/md2pdf
	@echo ""
	@echo "✅ md2pdf installed."
	@echo "   Location: $(PREFIX)/bin/md2pdf"
	@echo "   Venv:     $(PREFIX)/share/md2pdf/.venv"
	@echo ""
	@if echo "$$PATH" | grep -q "$(PREFIX)/bin"; then \
		echo "   Ready to use: md2pdf --help"; \
	else \
		echo "   Add to your PATH:"; \
		echo "   export PATH=\"$(PREFIX)/bin:\$$PATH\""; \
	fi

uninstall-system: ## Remove system-wide installation
	@if [ ! -w "$(PREFIX)/bin/md2pdf" ] 2>/dev/null && [ ! -w "$(PREFIX)/share/md2pdf" ] 2>/dev/null; then \
		echo "❌ Cannot write to $(PREFIX). Run with sudo:"; \
		echo "   sudo make uninstall-system"; \
		exit 1; \
	fi
	@echo "🗑️  Removing md2pdf from $(PREFIX)..."
	@rm -f $(PREFIX)/bin/md2pdf
	@rm -rf $(PREFIX)/share/md2pdf
	@echo "✅ md2pdf removed from $(PREFIX)."

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
