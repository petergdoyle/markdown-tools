"""Markdown → HTML → PDF conversion pipeline."""

from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

from md2pdf.styles import DEFAULT_CSS


@dataclass
class ConversionResult:
    """Result of a single markdown-to-PDF conversion."""

    source: Path
    output: Path
    success: bool
    error: str | None = None


def markdown_to_html(content: str) -> str:
    """Convert markdown text to HTML using markdown-it-py.

    Supports: headings, paragraphs, lists, code blocks (fenced + indented),
    blockquotes, tables, links, images, emphasis, horizontal rules, footnotes,
    and task lists.

    Args:
        content: Raw markdown text.

    Returns:
        HTML string.
    """
    md = MarkdownIt("commonmark", {"typographer": True})
    md.enable("table")
    md.enable("strikethrough")
    footnote_plugin(md)
    tasklists_plugin(md)

    return md.render(content)


def html_to_pdf(html: str, output_path: Path, css: str) -> None:
    """Render HTML string to PDF file using WeasyPrint with the given CSS.

    Creates parent directories of output_path if they don't exist.

    Args:
        html: The HTML content to render.
        output_path: Path where the PDF file will be written.
        css: CSS stylesheet to apply to the HTML.
    """
    from weasyprint import CSS, HTML

    output_path.parent.mkdir(parents=True, exist_ok=True)

    html_doc = HTML(string=html)
    stylesheet = CSS(string=css)
    html_doc.write_pdf(output_path, stylesheets=[stylesheet])


def convert_markdown_to_pdf(source: Path, output: Path) -> ConversionResult:
    """Convert a single markdown file to PDF.

    Pipeline: markdown → HTML (via markdown-it-py) → PDF (via weasyprint)

    This function never raises. All errors are captured in the returned
    ConversionResult.

    Args:
        source: Path to the .md source file.
        output: Path where the .pdf file will be written.

    Returns:
        ConversionResult indicating success or failure with error details.
    """
    try:
        content = source.read_text(encoding="utf-8")
        html = markdown_to_html(content)
        html_to_pdf(html, output, DEFAULT_CSS)
        return ConversionResult(source=source, output=output, success=True)
    except Exception as e:
        return ConversionResult(
            source=source, output=output, success=False, error=str(e)
        )
