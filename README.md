# markdown-tools

A collection of Python CLI utilities for working with markdown files.

## Available Utilities

| Utility | Description |
|---------|-------------|
| `md2pdf` | Convert markdown files to PDF |

## md2pdf

Converts one or more markdown files to PDF using a markdown → HTML → PDF rendering pipeline. Supports single files, directories, and recursive directory traversal with depth control.

**Images & diagrams:**
- **Relative images** (`![](pic.png)`, `![](images/x.png)`) render — paths resolve against the source file's directory.
- **Mermaid diagrams** (` ```mermaid ` fenced blocks) render to embedded PNG images when the [mermaid CLI](https://github.com/mermaid-js/mermaid-cli) (`mmdc`) is installed (`npm install -g @mermaid-js/mermaid-cli`). Large diagrams are scaled to fit the page (never overflow or clip). Without `mmdc`, the block is left as a code block — nothing breaks.

### CLI Usage

```bash
# Convert a single file
md2pdf document.md

# Convert all markdown files in a directory
md2pdf ./docs

# Specify an output directory
md2pdf ./docs --output ./pdfs

# Limit directory recursion depth
md2pdf ./docs --depth 2

# Combine options
md2pdf ./docs --output ./pdfs --depth 3
```

**Arguments:**

- `SOURCE` — A markdown file (`.md`) or a directory containing markdown files (positional, required)

**Options:**

- `--output`, `-o` — Output directory for generated PDFs (default: `./output`)
- `--depth`, `-d` — Maximum directory recursion depth (default: unlimited)

### Makefile Usage

The Makefile provides a convenient front-end for development:

```bash
# Convert with defaults (current directory → ./output, unlimited depth)
make md2pdf

# Specify source, output, and depth
make md2pdf SOURCE=./docs OUTPUT=./pdfs DEPTH=3
```

### Installation

**Use `make install`.** From a clone of this repo:

```bash
make install
```

That single command does everything md2pdf needs — and unlike `markdown-to-jira`
/ `markdown-to-confluence`, md2pdf has a **native C dependency** (WeasyPrint →
pango), which a bare `uv tool install` does *not* set up. `make install`:

1. installs pango via Homebrew if it's missing;
2. installs the tool from **current source** (`uv tool install --force --reinstall
   --no-cache` — the `--no-cache` matters: the version stays `0.1.0` between edits,
   so a plain install would silently reuse a stale cached build and ship old code);
3. writes a launcher at `~/.local/bin/md2pdf` that puts pango on the dynamic-load
   path (`DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"`) so WeasyPrint loads.

Run it again any time you pull new code — it's idempotent and always installs the
latest.

> **Why not `uv tool install git+ssh://…`?** It works for the other two tools, but
> for md2pdf it installs the Python code **without** the pango launcher, so you'll
> hit `cannot load library 'libpango-1.0-0'` at runtime. If you must install that
> way, also `brew install pango` and wrap the binary so
> `DYLD_FALLBACK_LIBRARY_PATH` includes `$(brew --prefix)/lib`. `make install` is
> the supported path.

After install, `md2pdf` is available from any terminal session. If your shell can't find it, add `~/.local/bin` to your PATH:

```bash

After install, `md2pdf` is available from any terminal session. If your shell can't find it, add `~/.local/bin` to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

To remove:

```bash
make uninstall
```

#### System-wide (shared prefix)

Installs `md2pdf` to a shared location so multiple users (or just a cleaner install) can use it. Only requires `sudo` if you don't own the target directory.

```bash
# Install to /usr/local/bin (needs sudo on most systems)
sudo make install-system

# Install to a directory you own (no sudo needed)
make install-system PREFIX=/opt/md2pdf

# Any custom prefix works
make install-system PREFIX=~/tools
```

This creates an isolated Python virtual environment at `PREFIX/share/md2pdf/.venv` and symlinks the binary into `PREFIX/bin`. If `PREFIX/bin` isn't already on your PATH, the installer will tell you what to add.

To remove:

```bash
make uninstall-system                        # if you own the prefix
sudo make uninstall-system                   # if you don't
make uninstall-system PREFIX=/opt/md2pdf     # match the PREFIX you used
```

#### System dependencies

Both install methods require **pango** (used by WeasyPrint for text rendering):

```bash
# macOS
brew install pango

# Debian / Ubuntu
sudo apt install libpango1.0-dev
```

The `make install` target will auto-install pango via Homebrew if missing. The `make install-system` target will prompt you to install it manually.

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
