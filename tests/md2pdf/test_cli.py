"""CLI integration tests for md2pdf using click.testing.CliRunner."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from md2pdf.cli import main
from md2pdf.converter import ConversionResult


def mock_convert_success(source: Path, output: Path) -> ConversionResult:
    """Mock converter that always succeeds and creates a fake PDF."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"%PDF-1.4 fake")
    return ConversionResult(source=source, output=output, success=True)


def mock_convert_failure(source: Path, output: Path) -> ConversionResult:
    """Mock converter that always fails."""
    return ConversionResult(
        source=source, output=output, success=False, error="Rendering error"
    )


class TestHelpOutput:
    """Test --help shows usage information."""

    def test_help_shows_usage(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "SOURCE" in result.output
        assert "--output" in result.output
        assert "--depth" in result.output


class TestInvalidInputs:
    """Test error handling for invalid inputs."""

    def test_non_existent_source_path(self, tmp_path: Path):
        runner = CliRunner()
        non_existent = str(tmp_path / "does_not_exist")
        result = runner.invoke(main, [non_existent])
        assert result.exit_code == 1
        assert "\u274c" in result.output
        assert "does not exist" in result.output

    def test_non_md_source_file(self, tmp_path: Path):
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("Just text.", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, [str(txt_file)])
        assert result.exit_code == 1
        assert "\u274c" in result.output
        assert "not a markdown file" in result.output


class TestEmptyDirectory:
    """Test behavior when no markdown files are found."""

    def test_empty_directory_exits_zero(self, tmp_path: Path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        runner = CliRunner()
        result = runner.invoke(main, [str(empty_dir)])
        assert result.exit_code == 0
        assert "\u2139\ufe0f" in result.output
        assert "No markdown files found" in result.output

    def test_directory_with_only_non_md_files(self, tmp_path: Path):
        dir_path = tmp_path / "nomd"
        dir_path.mkdir()
        (dir_path / "readme.txt").write_text("text", encoding="utf-8")
        (dir_path / "data.csv").write_text("a,b,c", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, [str(dir_path)])
        assert result.exit_code == 0
        assert "No markdown files found" in result.output


class TestSingleFileConversion:
    """Test converting a single markdown file."""

    @patch("md2pdf.cli.convert_markdown_to_pdf", side_effect=mock_convert_success)
    def test_single_file_success(self, mock_conv, tmp_md_file: Path, tmp_path: Path):
        output_dir = tmp_path / "pdf_out"
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_md_file), "--output", str(output_dir)])
        assert result.exit_code == 0
        assert "\U0001f4c4 Converting" in result.output
        assert "\U0001f4ca Converted" in result.output
        assert "1/1" in result.output
        mock_conv.assert_called_once()


class TestDirectoryConversion:
    """Test converting a directory of markdown files."""

    @patch("md2pdf.cli.convert_markdown_to_pdf", side_effect=mock_convert_success)
    def test_directory_converts_multiple_files(
        self, mock_conv, tmp_md_dir: Path, tmp_path: Path
    ):
        output_dir = tmp_path / "pdf_out"
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_md_dir), "--output", str(output_dir)])
        assert result.exit_code == 0
        # tmp_md_dir has 4 .md files: top1.md, top2.md, sub1/nested1.md, sub1/sub2/deep1.md
        assert mock_conv.call_count == 4
        assert "\U0001f4c4 Converting" in result.output
        assert "4/4" in result.output


class TestDepthFiltering:
    """Test --depth flag limits recursion."""

    @patch("md2pdf.cli.convert_markdown_to_pdf", side_effect=mock_convert_success)
    def test_depth_one_only_top_level(
        self, mock_conv, tmp_md_dir: Path, tmp_path: Path
    ):
        output_dir = tmp_path / "pdf_out"
        runner = CliRunner()
        result = runner.invoke(
            main, [str(tmp_md_dir), "--output", str(output_dir), "--depth", "1"]
        )
        assert result.exit_code == 0
        # Depth 1 = only top-level files: top1.md, top2.md
        assert mock_conv.call_count == 2
        assert "top1" in result.output
        assert "top2" in result.output
        # Nested files should not appear
        assert "deep1" not in result.output


class TestOutputDirectoryCreation:
    """Test that a non-existent output directory gets created."""

    @patch("md2pdf.cli.convert_markdown_to_pdf", side_effect=mock_convert_success)
    def test_output_directory_created(self, mock_conv, tmp_md_file: Path, tmp_path: Path):
        output_dir = tmp_path / "brand_new" / "nested" / "output"
        assert not output_dir.exists()
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_md_file), "--output", str(output_dir)])
        assert result.exit_code == 0
        # The mock_convert_success creates parent dirs when writing the fake PDF
        # Verify the mock was called with the expected output path under output_dir
        call_args = mock_conv.call_args
        assert str(output_dir) in str(call_args)


class TestErrorIsolation:
    """Test that one file failure doesn't stop other files from processing."""

    def test_one_failure_others_continue(self, tmp_md_dir: Path, tmp_path: Path):
        output_dir = tmp_path / "pdf_out"
        call_count = {"n": 0}

        def mock_convert_mixed(source: Path, output: Path) -> ConversionResult:
            """Fail on the first file, succeed on others."""
            call_count["n"] += 1
            if call_count["n"] == 1:
                return ConversionResult(
                    source=source,
                    output=output,
                    success=False,
                    error="Permission denied",
                )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"%PDF-1.4 fake")
            return ConversionResult(source=source, output=output, success=True)

        with patch("md2pdf.cli.convert_markdown_to_pdf", side_effect=mock_convert_mixed):
            runner = CliRunner()
            result = runner.invoke(
                main, [str(tmp_md_dir), "--output", str(output_dir)]
            )
            assert result.exit_code == 0
            # All 4 files were attempted
            assert call_count["n"] == 4
            # One failure reported
            assert "\u274c" in result.output
            assert "Permission denied" in result.output
            # Three successes plus the failure = 4 total mentioned in summary
            assert "3/4" in result.output


class TestSummaryCount:
    """Test that the summary line accurately reports conversion counts."""

    @patch("md2pdf.cli.convert_markdown_to_pdf", side_effect=mock_convert_success)
    def test_summary_all_success(self, mock_conv, tmp_md_dir: Path, tmp_path: Path):
        output_dir = tmp_path / "pdf_out"
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_md_dir), "--output", str(output_dir)])
        assert "\U0001f4ca Converted 4/4 files" in result.output

    @patch("md2pdf.cli.convert_markdown_to_pdf", side_effect=mock_convert_failure)
    def test_summary_all_failure(self, mock_conv, tmp_md_dir: Path, tmp_path: Path):
        output_dir = tmp_path / "pdf_out"
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_md_dir), "--output", str(output_dir)])
        assert "\U0001f4ca Converted 0/4 files" in result.output

    def test_summary_partial_success(self, tmp_md_dir: Path, tmp_path: Path):
        output_dir = tmp_path / "pdf_out"
        call_count = {"n": 0}

        def mock_convert_alternating(source: Path, output: Path) -> ConversionResult:
            """Alternate between success and failure."""
            call_count["n"] += 1
            if call_count["n"] % 2 == 0:
                return ConversionResult(
                    source=source,
                    output=output,
                    success=False,
                    error="Oops",
                )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"%PDF-1.4 fake")
            return ConversionResult(source=source, output=output, success=True)

        with patch(
            "md2pdf.cli.convert_markdown_to_pdf", side_effect=mock_convert_alternating
        ):
            runner = CliRunner()
            result = runner.invoke(
                main, [str(tmp_md_dir), "--output", str(output_dir)]
            )
            # 4 files, alternating: succeed, fail, succeed, fail → 2 successes
            assert "\U0001f4ca Converted 2/4 files" in result.output
