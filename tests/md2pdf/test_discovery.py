"""Unit tests for the md2pdf discovery module."""

from pathlib import Path

import pytest

from md2pdf.discovery import discover_markdown_files


class TestSingleFileInput:
    """Tests for passing a single .md file as source."""

    def test_single_md_file_returns_list_with_that_file(self, tmp_md_file: Path):
        """Passing a .md file returns a list containing that file."""
        result = discover_markdown_files(tmp_md_file)
        assert result == [tmp_md_file.resolve()]

    def test_single_md_file_returns_exactly_one_item(self, tmp_md_file: Path):
        """Passing a .md file returns a list of length 1."""
        result = discover_markdown_files(tmp_md_file)
        assert len(result) == 1


class TestDirectoryInput:
    """Tests for passing a directory as source."""

    def test_directory_finds_all_md_files_recursively(self, tmp_md_dir: Path):
        """A directory with nested .md files finds all of them."""
        result = discover_markdown_files(tmp_md_dir)
        # tmp_md_dir has: top1.md, top2.md, sub1/nested1.md, sub1/sub2/deep1.md
        assert len(result) == 4

    def test_directory_results_are_sorted(self, tmp_md_dir: Path):
        """Results from a directory scan are sorted alphabetically."""
        result = discover_markdown_files(tmp_md_dir)
        assert result == sorted(result)

    def test_directory_returns_only_md_files(self, tmp_md_dir: Path):
        """Only .md files are returned, not .txt or other extensions."""
        result = discover_markdown_files(tmp_md_dir)
        for path in result:
            assert path.suffix.lower() == ".md"


class TestNonMdFilesSkipped:
    """Tests for filtering out non-.md files."""

    def test_txt_files_not_included(self, tmp_md_dir: Path):
        """A .txt file in the directory tree is not returned."""
        result = discover_markdown_files(tmp_md_dir)
        txt_files = [p for p in result if p.suffix == ".txt"]
        assert txt_files == []

    def test_non_md_files_excluded_from_results(self, tmp_path: Path):
        """Various non-.md extensions are excluded from discovery."""
        (tmp_path / "doc.md").write_text("# Markdown\n", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("text\n", encoding="utf-8")
        (tmp_path / "report.pdf").write_bytes(b"%PDF-1.4")
        (tmp_path / "data.json").write_text("{}\n", encoding="utf-8")

        result = discover_markdown_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "doc.md"


class TestDepthFiltering:
    """Tests for the max_depth parameter."""

    def test_depth_1_finds_only_top_level_files(self, tmp_md_dir: Path):
        """depth=1 returns only files directly in the source directory."""
        result = discover_markdown_files(tmp_md_dir, max_depth=1)
        # Only top1.md and top2.md are at depth 1
        assert len(result) == 2
        names = {p.name for p in result}
        assert names == {"top1.md", "top2.md"}

    def test_depth_2_finds_files_up_to_one_subdirectory(self, tmp_md_dir: Path):
        """depth=2 returns files at top-level and one subdirectory deep."""
        result = discover_markdown_files(tmp_md_dir, max_depth=2)
        # top1.md, top2.md (depth 1) + sub1/nested1.md (depth 2)
        assert len(result) == 3
        names = {p.name for p in result}
        assert names == {"top1.md", "top2.md", "nested1.md"}

    def test_depth_none_finds_all_files_unlimited(self, tmp_md_dir: Path):
        """depth=None (default) finds all .md files at any depth."""
        result = discover_markdown_files(tmp_md_dir, max_depth=None)
        # All 4 .md files: top1, top2, nested1, deep1
        assert len(result) == 4

    def test_depth_3_includes_deeply_nested_files(self, tmp_md_dir: Path):
        """depth=3 finds the deepest file (sub1/sub2/deep1.md at depth 3)."""
        result = discover_markdown_files(tmp_md_dir, max_depth=3)
        assert len(result) == 4
        names = {p.name for p in result}
        assert "deep1.md" in names


class TestNonExistentPath:
    """Tests for handling of non-existent paths."""

    def test_raises_file_not_found_error(self, tmp_path: Path):
        """A non-existent path raises FileNotFoundError."""
        fake_path = tmp_path / "does_not_exist.md"
        with pytest.raises(FileNotFoundError):
            discover_markdown_files(fake_path)

    def test_non_existent_directory_raises_file_not_found(self, tmp_path: Path):
        """A non-existent directory path raises FileNotFoundError."""
        fake_dir = tmp_path / "no_such_directory"
        with pytest.raises(FileNotFoundError):
            discover_markdown_files(fake_dir)


class TestNonMdSingleFile:
    """Tests for passing a non-.md single file as source."""

    def test_raises_value_error_for_txt_file(self, tmp_non_md_file: Path):
        """A .txt file raises ValueError."""
        with pytest.raises(ValueError, match="not a markdown file"):
            discover_markdown_files(tmp_non_md_file)

    def test_raises_value_error_for_pdf_file(self, tmp_path: Path):
        """A .pdf file raises ValueError."""
        pdf_file = tmp_path / "report.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        with pytest.raises(ValueError, match="not a markdown file"):
            discover_markdown_files(pdf_file)


class TestEmptyDirectory:
    """Tests for empty directories."""

    def test_empty_directory_returns_empty_list(self, tmp_empty_dir: Path):
        """An empty directory returns an empty list."""
        result = discover_markdown_files(tmp_empty_dir)
        assert result == []

    def test_directory_with_no_md_files_returns_empty(self, tmp_path: Path):
        """A directory with files but no .md files returns an empty list."""
        (tmp_path / "notes.txt").write_text("text\n", encoding="utf-8")
        (tmp_path / "data.json").write_text("{}\n", encoding="utf-8")
        result = discover_markdown_files(tmp_path)
        assert result == []


class TestCaseInsensitiveExtension:
    """Tests for case-insensitive .md extension matching."""

    def test_uppercase_md_extension_is_included(self, tmp_path: Path):
        """A file with .MD extension is discovered."""
        md_file = tmp_path / "README.MD"
        md_file.write_text("# Title\n", encoding="utf-8")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "README.MD"

    def test_mixed_case_md_extension_is_included(self, tmp_path: Path):
        """A file with .Md extension is discovered."""
        md_file = tmp_path / "notes.Md"
        md_file.write_text("# Notes\n", encoding="utf-8")
        result = discover_markdown_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "notes.Md"

    def test_single_file_with_uppercase_extension(self, tmp_path: Path):
        """Passing a single file with .MD extension works correctly."""
        md_file = tmp_path / "DOC.MD"
        md_file.write_text("# Doc\n", encoding="utf-8")
        result = discover_markdown_files(md_file)
        assert result == [md_file.resolve()]
