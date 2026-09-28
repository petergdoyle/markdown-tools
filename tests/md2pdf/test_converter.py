"""Unit tests for the md2pdf converter module.

Tests cover markdown_to_html rendering for various elements and
convert_markdown_to_pdf success/error handling.

Requirements: 6.1, 6.2, 6.3
"""

from unittest.mock import patch

import pytest

from md2pdf.converter import ConversionResult, convert_markdown_to_pdf, markdown_to_html

# --- Helper for WeasyPrint availability ---

def weasyprint_available():
    try:
        from weasyprint import HTML
        HTML(string="<p>test</p>").write_pdf()
        return True
    except Exception:
        return False


requires_weasyprint = pytest.mark.skipif(
    not weasyprint_available(),
    reason="WeasyPrint system libraries not available",
)


# --- Tests for markdown_to_html ---


class TestMarkdownToHtmlHeadings:
    """markdown_to_html renders headings."""

    def test_h1(self):
        result = markdown_to_html("# Hello")
        assert "<h1>Hello</h1>" in result

    def test_h2(self):
        result = markdown_to_html("## Subtitle")
        assert "<h2>Subtitle</h2>" in result

    def test_h3(self):
        result = markdown_to_html("### Third Level")
        assert "<h3>Third Level</h3>" in result


class TestMarkdownToHtmlParagraphs:
    """markdown_to_html renders paragraphs."""

    def test_plain_text_wrapped_in_p(self):
        result = markdown_to_html("Hello world")
        assert "<p>Hello world</p>" in result

    def test_multiple_paragraphs(self):
        result = markdown_to_html("First paragraph.\n\nSecond paragraph.")
        assert "<p>First paragraph.</p>" in result
        assert "<p>Second paragraph.</p>" in result


class TestMarkdownToHtmlLists:
    """markdown_to_html renders unordered and ordered lists."""

    def test_unordered_list(self):
        md = "- Item one\n- Item two\n- Item three"
        result = markdown_to_html(md)
        assert "<ul>" in result
        assert "<li>Item one</li>" in result
        assert "<li>Item two</li>" in result
        assert "<li>Item three</li>" in result

    def test_ordered_list(self):
        md = "1. First\n2. Second\n3. Third"
        result = markdown_to_html(md)
        assert "<ol>" in result
        assert "<li>First</li>" in result
        assert "<li>Second</li>" in result
        assert "<li>Third</li>" in result


class TestMarkdownToHtmlCodeBlocks:
    """markdown_to_html renders fenced code blocks."""

    def test_fenced_code_block(self):
        md = '```python\ndef hello():\n    print("Hello")\n```'
        result = markdown_to_html(md)
        assert "<pre>" in result
        assert "<code" in result
        assert "def hello():" in result

    def test_inline_code(self):
        md = "Use `print()` to output text."
        result = markdown_to_html(md)
        assert "<code>print()</code>" in result


class TestMarkdownToHtmlBlockquotes:
    """markdown_to_html renders blockquotes."""

    def test_blockquote(self):
        md = "> This is a blockquote."
        result = markdown_to_html(md)
        assert "<blockquote>" in result
        assert "This is a blockquote." in result


class TestMarkdownToHtmlTables:
    """markdown_to_html renders pipe tables."""

    def test_table_structure(self):
        md = "| Name | Age |\n|------|-----|\n| Alice | 30 |\n| Bob | 25 |"
        result = markdown_to_html(md)
        assert "<table>" in result
        assert "<th>" in result
        assert "<td>" in result
        assert "Alice" in result
        assert "Bob" in result


class TestMarkdownToHtmlLinks:
    """markdown_to_html renders links."""

    def test_link(self):
        md = "[Example](https://example.com)"
        result = markdown_to_html(md)
        assert '<a href="https://example.com"' in result
        assert "Example</a>" in result


class TestMarkdownToHtmlFullSample:
    """markdown_to_html handles a full sample document with all element types."""

    def test_full_sample(self, sample_markdown):
        result = markdown_to_html(sample_markdown)
        # Headings
        assert "<h1>" in result
        assert "<h2>" in result
        # Paragraphs
        assert "<p>" in result
        # Lists
        assert "<ul>" in result
        assert "<ol>" in result
        # Code
        assert "<pre>" in result
        assert "<code" in result
        # Blockquote
        assert "<blockquote>" in result
        # Table
        assert "<table>" in result
        assert "<th>" in result
        assert "<td>" in result
        # Links
        assert "<a " in result
        # Images
        assert "<img" in result
        # Bold/italic
        assert "<strong>" in result
        assert "<em>" in result


# --- Tests for convert_markdown_to_pdf ---


class TestConvertMarkdownToPdfSuccess:
    """convert_markdown_to_pdf returns success with valid input."""

    @requires_weasyprint
    def test_success_with_weasyprint(self, tmp_md_file, output_dir):
        output_path = output_dir / "sample.pdf"
        result = convert_markdown_to_pdf(tmp_md_file, output_path)

        assert result.success is True
        assert result.error is None
        assert result.source == tmp_md_file
        assert result.output == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_success_with_mocked_html_to_pdf(self, tmp_md_file, output_dir):
        """Tests the conversion pipeline with html_to_pdf mocked out."""
        output_path = output_dir / "sample.pdf"

        def fake_html_to_pdf(html, out_path, css, base_url=None):
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(b"%PDF-1.4 fake content")

        with patch("md2pdf.converter.html_to_pdf", side_effect=fake_html_to_pdf):
            result = convert_markdown_to_pdf(tmp_md_file, output_path)

        assert result.success is True
        assert result.error is None
        assert result.source == tmp_md_file
        assert result.output == output_path
        assert output_path.exists()


class TestConvertMarkdownToPdfErrorHandling:
    """convert_markdown_to_pdf handles errors gracefully."""

    def test_nonexistent_source_file(self, tmp_path):
        source = tmp_path / "does_not_exist.md"
        output = tmp_path / "out.pdf"

        result = convert_markdown_to_pdf(source, output)

        assert result.success is False
        assert result.error is not None
        assert isinstance(result, ConversionResult)
        assert result.source == source
        assert result.output == output

    def test_unreadable_file(self, tmp_path):
        """A file that cannot be read returns an error result."""
        source = tmp_path / "unreadable.md"
        source.write_text("# Test", encoding="utf-8")
        source.chmod(0o000)
        output = tmp_path / "out.pdf"

        result = convert_markdown_to_pdf(source, output)

        assert result.success is False
        assert result.error is not None

        # Restore permissions for cleanup
        source.chmod(0o644)


class TestConvertMarkdownToPdfCreatesParentDirs:
    """convert_markdown_to_pdf creates parent directories for output."""

    def test_creates_nested_output_directories(self, tmp_md_file, tmp_path):
        """Output in a nested non-existent directory still works."""
        output_path = tmp_path / "a" / "b" / "c" / "sample.pdf"
        assert not output_path.parent.exists()

        def fake_html_to_pdf(html, out_path, css, base_url=None):
            # html_to_pdf is responsible for creating parent dirs
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(b"%PDF-1.4 fake content")

        with patch("md2pdf.converter.html_to_pdf", side_effect=fake_html_to_pdf):
            result = convert_markdown_to_pdf(tmp_md_file, output_path)

        assert result.success is True
        assert output_path.parent.exists()
        assert output_path.exists()

    @requires_weasyprint
    def test_creates_nested_directories_real(self, tmp_md_file, tmp_path):
        """With real WeasyPrint, output directories are created."""
        output_path = tmp_path / "deep" / "nested" / "dir" / "sample.pdf"
        assert not output_path.parent.exists()

        result = convert_markdown_to_pdf(tmp_md_file, output_path)

        assert result.success is True
        assert output_path.exists()
        assert output_path.parent.exists()


# --- Tests for relative-image rendering (base_url wiring) ---
def _make_png(path):
    """Write a minimal valid 8x8 red PNG."""
    import struct
    import zlib

    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    w = h = 8
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


class TestRelativeImageRendering:
    """convert_markdown_to_pdf resolves relative image paths via base_url."""

    def test_base_url_is_passed_to_html_to_pdf(self, tmp_path):
        """The source file's directory is threaded as the base_url so relative
        images resolve (regression guard for the missing-base_url image bug)."""
        src = tmp_path / "doc.md"
        src.write_text("# T\n\n![a](pic.png)\n", encoding="utf-8")
        captured = {}

        def fake_html_to_pdf(html, out_path, css, base_url=None):
            captured["base_url"] = base_url
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(b"%PDF-1.4")

        with patch("md2pdf.converter.html_to_pdf", side_effect=fake_html_to_pdf):
            result = convert_markdown_to_pdf(src, tmp_path / "out.pdf")

        assert result.success is True
        assert captured["base_url"], "base_url must be set"
        # Points at the source file's directory as a file:// URL.
        assert captured["base_url"].startswith("file://")
        assert captured["base_url"].rstrip("/").endswith(str(tmp_path.resolve()).replace("\\", "/"))

    @requires_weasyprint
    def test_relative_image_renders_without_base_uri_warning(self, tmp_path):
        import logging

        _make_png(tmp_path / "pic.png")
        (tmp_path / "doc.md").write_text("# T\n\n![a](pic.png)\n", encoding="utf-8")

        msgs: list[str] = []
        handler = logging.Handler()
        handler.emit = lambda r: msgs.append(r.getMessage())
        logger = logging.getLogger("weasyprint")
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        try:
            result = convert_markdown_to_pdf(tmp_path / "doc.md", tmp_path / "out.pdf")
        finally:
            logger.removeHandler(handler)

        assert result.success is True, result.error
        assert not any("base URI" in m for m in msgs), f"image did not resolve: {msgs}"


# --- Tests for mermaid → embedded image rendering ---
def _mmdc_available():
    from md2pdf import mermaid

    return mermaid.available()


requires_mmdc = pytest.mark.skipif(not _mmdc_available(), reason="mermaid CLI (mmdc) not installed")


class TestMermaidRendering:
    """```mermaid``` fences become embedded <img> diagrams in the PDF."""

    def test_no_mermaid_is_noop(self, tmp_path):
        from md2pdf.converter import render_mermaid_blocks

        html = "<p>no diagrams here</p>"
        out, rendered, failed = render_mermaid_blocks(html, tmp_path / "unused")
        assert out == html and rendered == 0 and failed == 0

    def test_missing_mmdc_leaves_code_block(self, tmp_path, monkeypatch):
        """Without mmdc, the mermaid code block is left untouched (graceful)."""
        from md2pdf import converter

        monkeypatch.setattr(converter.mermaid, "available", lambda *a, **k: False)
        html = '<pre><code class="language-mermaid">flowchart LR\n A--&gt;B</code></pre>'
        out, rendered, failed = converter.render_mermaid_blocks(html, tmp_path / "imgs")
        assert out == html and rendered == 0 and failed == 0

    def test_render_failure_keeps_code_block(self, tmp_path, monkeypatch):
        """A diagram that fails to render is counted failed and left as code."""
        from md2pdf import converter

        monkeypatch.setattr(converter.mermaid, "available", lambda *a, **k: True)

        def _boom(*a, **k):
            raise converter.mermaid.MermaidError("bad diagram")

        monkeypatch.setattr(converter.mermaid, "render_png", _boom)
        html = '<pre><code class="language-mermaid">nonsense</code></pre>'
        out, rendered, failed = converter.render_mermaid_blocks(html, tmp_path / "imgs")
        assert rendered == 0 and failed == 1
        assert "language-mermaid" in out  # original code block preserved

    @requires_mmdc
    def test_mermaid_block_becomes_image(self, tmp_path):
        from md2pdf.converter import markdown_to_html, render_mermaid_blocks

        html = markdown_to_html("```mermaid\nflowchart LR\n A-->B\n```\n")
        out, rendered, failed = render_mermaid_blocks(html, tmp_path / "imgs")
        assert rendered == 1 and failed == 0
        assert 'class="mermaid-diagram"' in out
        assert "language-mermaid" not in out
        # A PNG was written and referenced by absolute file URL.
        pngs = list((tmp_path / "imgs").glob("mermaid-*.png"))
        assert len(pngs) == 1

    @requires_mmdc
    @requires_weasyprint
    def test_full_pipeline_embeds_mermaid(self, tmp_path):
        from md2pdf.converter import convert_markdown_to_pdf

        (tmp_path / "d.md").write_text(
            "# T\n\n```mermaid\nflowchart LR\n A-->B-->C\n```\n", encoding="utf-8"
        )
        r = convert_markdown_to_pdf(tmp_path / "d.md", tmp_path / "out.pdf")
        assert r.success is True, r.error
        assert (tmp_path / "out.pdf").stat().st_size > 0
