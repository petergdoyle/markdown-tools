"""Render Mermaid diagrams to PNG via the mermaid CLI (``mmdc``).

Markdown ```mermaid``` fenced blocks are otherwise emitted as plain code by the
Markdown renderer and never become diagrams in the PDF. When ``mmdc`` is present
we render each fence to a **PNG** and swap it into the HTML as an ``<img>`` so
WeasyPrint embeds a real diagram. Adapted from markdown-to-confluence's mermaid
module — same content-hash keying and graceful degradation.

Degrades gracefully: if ``mmdc`` isn't installed, ``available()`` is False and
callers keep the original code block. Rendering is keyed by a content hash so an
identical diagram always produces the same filename (cache-friendly, idempotent).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_MMDC = "mmdc"
# In containers/CI, headless Chromium needs --no-sandbox; point this env var at a
# Puppeteer JSON config, e.g. {"args":["--no-sandbox","--disable-setuid-sandbox"]}.
_PUPPETEER_CONFIG_ENV = "MERMAID_PUPPETEER_CONFIG"


def available(mmdc: str = _MMDC) -> bool:
    """True if the mermaid CLI is on PATH (rendering is possible)."""
    return shutil.which(mmdc) is not None


def diagram_digest(source: str) -> str:
    """Stable short hash of the diagram source — the image filename stem."""
    return hashlib.sha256(source.strip().encode("utf-8")).hexdigest()[:12]


class MermaidError(RuntimeError):
    """Rendering failed (bad diagram syntax, missing Chromium, etc.)."""


def render_png(
    source: str,
    out_path: Path,
    *,
    scale: int = 2,
    background: str = "white",
    theme: str = "neutral",
    mmdc: str = _MMDC,
    timeout: float = 60.0,
    puppeteer_config: str | None = None,
) -> Path:
    """Render one Mermaid diagram to a PNG at ``out_path``.

    ``scale`` > 1 gives a crisp raster that stays sharp when CSS scales it down to
    fit the page. Raises :class:`MermaidError` on failure.
    """
    if not available(mmdc):
        raise MermaidError(f"{mmdc} not found on PATH — install @mermaid-js/mermaid-cli")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False, encoding="utf-8") as f:
        f.write(source)
        in_path = Path(f.name)
    try:
        cmd = [
            mmdc,
            "-i", str(in_path),
            "-o", str(out_path),
            "-s", str(scale),
            "-b", background,
            "-t", theme,
        ]
        pconfig = puppeteer_config or os.environ.get(_PUPPETEER_CONFIG_ENV)
        if pconfig:
            cmd += ["-p", pconfig]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        if proc.returncode != 0 or not out_path.exists():
            raise MermaidError(
                f"mmdc failed (exit {proc.returncode}): "
                f"{proc.stderr.strip() or proc.stdout.strip()}"
            )
        return out_path
    except subprocess.TimeoutExpired as e:
        raise MermaidError(f"mmdc timed out after {timeout}s") from e
    finally:
        in_path.unlink(missing_ok=True)
