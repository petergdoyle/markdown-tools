# markdown-tools

A collection of Python CLI utilities for working with markdown files.

## Available Utilities

| Utility | Description |
|---------|-------------|
| `md2pdf` | Convert markdown files to PDF |

## md2pdf

Converts one or more markdown files to PDF using a markdown → HTML → PDF rendering pipeline. Supports single files, directories, and recursive directory traversal with depth control.

### CLI Usage

```bash
# Convert a single file
uv run md2pdf document.md

# Convert all markdown files in a directory
uv run md2pdf ./docs

# Specify an output directory
uv run md2pdf ./docs --output ./pdfs

# Limit directory recursion depth
uv run md2pdf ./docs --depth 2

# Combine options
uv run md2pdf ./docs --output ./pdfs --depth 3
```

**Arguments:**

- `SOURCE` — A markdown file (`.md`) or a directory containing markdown files (positional, required)

**Options:**

- `--output`, `-o` — Output directory for generated PDFs (default: `./output`)
- `--depth`, `-d` — Maximum directory recursion depth (default: unlimited)

### Makefile Usage

The Makefile provides a convenient front-end:

```bash
# Convert with defaults (current directory → ./output, unlimited depth)
make md2pdf

# Specify source, output, and depth
make md2pdf SOURCE=./docs OUTPUT=./pdfs DEPTH=3
```

## Development

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Install all dependencies
make setup
```

Or manually:

```bash
uv sync
```

### Running Tests

```bash
make test
```

### Linting

```bash
make lint
```

### Cleaning Output

```bash
make clean
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
