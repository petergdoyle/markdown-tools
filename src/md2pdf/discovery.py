"""File and directory discovery logic for md2pdf."""

from pathlib import Path


def _relative_depth(path: Path, root: Path) -> int:
    """Calculate the depth of path relative to root directory.

    Depth is measured as the number of directory levels between root and path's parent.
    A file directly inside root has depth 1.

    Args:
        path: The file path to measure.
        root: The root directory to measure from.

    Returns:
        The integer depth of path relative to root.
    """
    relative = path.relative_to(root)
    # Number of parts gives us the depth (file itself counts as one part)
    return len(relative.parts)


def discover_markdown_files(source: Path, max_depth: int | None = None) -> list[Path]:
    """Discover all .md files at the given source path.

    Args:
        source: A file path or directory path.
        max_depth: Maximum directory recursion depth. None means unlimited.
                   1 = top-level only (no subdirectories), 2 = one level of
                   subdirectories, etc.

    Returns:
        Sorted list of Path objects pointing to .md files.

    Raises:
        FileNotFoundError: If source does not exist.
        ValueError: If source is a file without .md extension.
    """
    source = source.resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    if source.is_file():
        if source.suffix.lower() != ".md":
            raise ValueError(
                f"Source file is not a markdown file: {source}"
            )
        return [source]

    # Source is a directory — walk and collect .md files
    results: list[Path] = []

    for path in source.rglob("*"):
        if not path.is_file():
            continue

        # Case-insensitive .md extension check
        if path.suffix.lower() != ".md":
            continue

        # Depth filtering
        if max_depth is not None:
            depth = _relative_depth(path, source)
            if depth > max_depth:
                continue

        results.append(path)

    return sorted(results)
