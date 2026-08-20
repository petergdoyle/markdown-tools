"""CLI entry point for md2pdf — markdown to PDF converter."""

import sys
from pathlib import Path

import click

from md2pdf.converter import convert_markdown_to_pdf
from md2pdf.discovery import discover_markdown_files


@click.command()
@click.argument("source", type=click.Path(exists=False))
@click.option(
    "--output",
    "-o",
    default="output",
    help="Output directory for PDFs.",
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=None,
    help="Max directory recursion depth.",
)
def main(source: str, output: str, depth: int | None) -> None:
    """Convert markdown files to PDF.

    SOURCE is a markdown file (.md) or directory containing markdown files.
    """
    source_path = Path(source).resolve()
    output_dir = Path(output).resolve()

    # Validate source path exists
    if not source_path.exists():
        click.echo(f"\u274c Source path does not exist: {source}")
        sys.exit(1)

    # Validate single-file source has .md extension
    if source_path.is_file() and source_path.suffix.lower() != ".md":
        click.echo(f"\u274c Source file is not a markdown file: {source}")
        sys.exit(1)

    # Discover markdown files
    files = discover_markdown_files(source_path, max_depth=depth)

    if not files:
        click.echo("\u2139\ufe0f  No markdown files found.")
        sys.exit(0)

    # Convert each file
    success_count = 0
    total_count = len(files)

    for file in files:
        # Compute relative path for display and output structure
        if source_path.is_file():
            relative = file.name
            output_path = output_dir / Path(file.name).with_suffix(".pdf")
        else:
            relative = file.relative_to(source_path)
            output_path = output_dir / relative.with_suffix(".pdf")

        click.echo(f"\U0001f4c4 Converting: {relative}")

        result = convert_markdown_to_pdf(file, output_path)

        if result.success:
            click.echo(f"\u2705 {output_path}")
            success_count += 1
        else:
            click.echo(f"\u274c Failed: {file} \u2014 {result.error}")

    # Summary
    click.echo(f"\U0001f4ca Converted {success_count}/{total_count} files")
