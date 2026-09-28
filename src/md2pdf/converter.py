"""Markdown → HTML → PDF conversion pipeline."""

import html as _html
import re
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

from md2pdf import mermaid
from md2pdf.styles import DEFAULT_CSS

# markdown-it renders a ```mermaid``` fence to <pre><code class="language-mermaid">…
# We match that block to swap in a rendered image. DOTALL for multi-line bodies.
_MERMAID_BLOCK = re.compile(
    r'<pre><code class="language-mermaid">(?P<body>.*?)</code></pre>',
    re.DOTALL,
)


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


def render_mermaid_blocks(html: str, image_dir: Path) -> tuple[str, int, int]:
    """Replace ```mermaid``` code blocks in ``html`` with rendered PNG ``<img>``s.

    Each block is rendered to ``image_dir/mermaid-<hash>.png`` and swapped for an
    ``<img class="mermaid-diagram" src="file://…">`` referencing it by absolute
    file URL (so it resolves regardless of the document base_url). The CSS scales
    the image to fit the page, so an oversized diagram shrinks rather than
    overflowing. Best-effort: a block that fails to render is left as-is (the
    original code block) and counted as failed — never fatal.

    Returns ``(html, rendered, failed)``. A no-op (and no mmdc call) when there
    are no mermaid blocks or the CLI isn't available.
    """
    if "language-mermaid" not in html:
        return html, 0, 0
    if not mermaid.available():
        return html, 0, 0

    image_dir.mkdir(parents=True, exist_ok=True)
    rendered = 0
    failed = 0

    def _replace(m: re.Match) -> str:
        nonlocal rendered, failed
        source = _html.unescape(m.group("body")).strip()
        try:
            out = image_dir / f"mermaid-{mermaid.diagram_digest(source)}.png"
            if not out.exists():
                mermaid.render_png(source, out)
            rendered += 1
            src = out.resolve().as_uri()
            return f'<img class="mermaid-diagram" src="{src}" alt="diagram" />'
        except mermaid.MermaidError:
            failed += 1
            return m.group(0)  # leave the original code block

    return _MERMAID_BLOCK.sub(_replace, html), rendered, failed


def html_to_pdf(html: str, output_path: Path, css: str, base_url: str | None = None) -> None:
    """Render HTML string to PDF file using WeasyPrint with the given CSS.

    Creates parent directories of output_path if they don't exist.

    Args:
        html: The HTML content to render.
        output_path: Path where the PDF file will be written.
        css: CSS stylesheet to apply to the HTML.
        base_url: Base URL/path WeasyPrint resolves relative resource references
            (``<img src="pic.png">``, local stylesheets, links) against. Without
            it, relative image paths cannot be resolved to the filesystem and the
            images are silently dropped. Pass the source markdown file's directory
            so ``![](pic.png)`` and ``![](images/x.png)`` resolve as authored.
    """
    from weasyprint import CSS, HTML

    output_path.parent.mkdir(parents=True, exist_ok=True)

    html_doc = HTML(string=html, base_url=base_url)
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
    import tempfile

    try:
        content = source.read_text(encoding="utf-8")
        html = markdown_to_html(content)
        # Resolve relative image paths (and other local resources) against the
        # source file's directory, so ``![](pic.png)`` renders. Without a base_url
        # WeasyPrint drops relative images ("Relative URI reference without a
        # base URI"). as_uri() gives a proper file:// base for the resolved dir.
        base_url = source.resolve().parent.as_uri() + "/"
        # Render ```mermaid``` fences to embedded PNGs (best-effort; no-op without
        # mmdc). Images go in a temp dir referenced by absolute file:// URLs, so
        # they survive until write_pdf reads them.
        with tempfile.TemporaryDirectory(prefix="md2pdf-mermaid-") as tmp:
            html, _rendered, _failed = render_mermaid_blocks(html, Path(tmp))
            html_to_pdf(html, output, DEFAULT_CSS, base_url=base_url)
        return ConversionResult(source=source, output=output, success=True)
    except Exception as e:
        return ConversionResult(
            source=source, output=output, success=False, error=str(e)
        )
