"""Shared pytest fixtures for md2pdf test suite."""

from pathlib import Path

import pytest

SAMPLE_MARKDOWN = """\
# Sample Document

This is a paragraph with **bold** and *italic* text.

## Lists

- Item one
- Item two
- Item three

1. First
2. Second
3. Third

## Code Block

```python
def hello():
    print("Hello, world!")
```

## Blockquote

> This is a blockquote with some wisdom.

## Table

| Name  | Age | City     |
|-------|-----|----------|
| Alice | 30  | Portland |
| Bob   | 25  | Seattle  |

## Links and Images

[Example link](https://example.com)

![Alt text](image.png)
"""


@pytest.fixture
def sample_markdown() -> str:
    """Return a string with sample markdown content covering headings,
    paragraphs, lists, code blocks, blockquotes, tables, links, and images."""
    return SAMPLE_MARKDOWN


@pytest.fixture
def tmp_md_file(tmp_path: Path) -> Path:
    """Create a temporary single .md file with sample markdown content."""
    md_file = tmp_path / "sample.md"
    md_file.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
    return md_file


@pytest.fixture
def tmp_md_dir(tmp_path: Path) -> Path:
    """Create a temporary directory tree with multiple .md files at different depths.

    Structure:
        root/
        +-- top1.md
        +-- top2.md
        +-- sub1/
        |   +-- nested1.md
        |   +-- sub2/
        |       +-- deep1.md
        +-- other/
            +-- file.txt  (non-.md file)
    """
    root = tmp_path / "root"
    root.mkdir()

    # Top-level .md files
    (root / "top1.md").write_text("# Top 1\n\nFirst top-level file.\n", encoding="utf-8")
    (root / "top2.md").write_text("# Top 2\n\nSecond top-level file.\n", encoding="utf-8")

    # Nested subdirectory with .md file
    sub1 = root / "sub1"
    sub1.mkdir()
    (sub1 / "nested1.md").write_text("# Nested 1\n\nOne level deep.\n", encoding="utf-8")

    # Deeper subdirectory
    sub2 = sub1 / "sub2"
    sub2.mkdir()
    (sub2 / "deep1.md").write_text("# Deep 1\n\nTwo levels deep.\n", encoding="utf-8")

    # Non-.md file in a sibling directory
    other = root / "other"
    other.mkdir()
    (other / "file.txt").write_text("This is not markdown.\n", encoding="utf-8")

    return root


@pytest.fixture
def tmp_empty_dir(tmp_path: Path) -> Path:
    """Create an empty temporary directory."""
    empty = tmp_path / "empty"
    empty.mkdir()
    return empty


@pytest.fixture
def tmp_non_md_file(tmp_path: Path) -> Path:
    """Create a temporary .txt file (not a markdown file)."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Just a plain text file.\n", encoding="utf-8")
    return txt_file


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for PDF output."""
    out = tmp_path / "pdf_output"
    out.mkdir()
    return out
