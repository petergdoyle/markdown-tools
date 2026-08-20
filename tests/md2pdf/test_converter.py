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

        def fake_html_to_pdf(html, out_path, css):
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

        def fake_html_to_pdf(html, out_path, css):
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
