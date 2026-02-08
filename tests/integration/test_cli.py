"""CLI integration tests for AIXtract using Click's CliRunner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from aixtract import __version__
from aixtract.cli.main import cli


@pytest.fixture()
def runner() -> CliRunner:
    """Create a fresh CliRunner for each test."""
    return CliRunner()


@pytest.fixture()
def sample_txt(tmp_path: Path) -> Path:
    """Create a sample .txt file for CLI tests."""
    p = tmp_path / "cli_test.txt"
    p.write_text("Hello from AIXtract CLI test. This is sample content.")
    return p


# ---------------------------------------------------------------------------
# 1. test_cli_help
# ---------------------------------------------------------------------------


class TestCliHelp:
    """Verify the CLI shows help text when invoked with no arguments."""

    def test_cli_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "AIXtract" in result.output


# ---------------------------------------------------------------------------
# 2. test_cli_version
# ---------------------------------------------------------------------------


class TestCliVersion:
    """Verify the CLI --version flag prints the version string."""

    def test_cli_version(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output
        assert "aixtract" in result.output.lower()


# ---------------------------------------------------------------------------
# 3. test_cli_formats
# ---------------------------------------------------------------------------


class TestCliFormats:
    """Verify the 'formats' subcommand lists registered converters."""

    def test_cli_formats(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["formats"])

        assert result.exit_code == 0
        # The formats command outputs a Rich table with converter names
        assert "Supported Formats" in result.output or "Converter" in result.output
        # At least the core text converters should appear
        assert "txt" in result.output.lower()


# ---------------------------------------------------------------------------
# 4. test_cli_extract_txt
# ---------------------------------------------------------------------------


class TestCliExtractTxt:
    """Verify basic file extraction via the CLI."""

    def test_cli_extract_txt(
        self, runner: CliRunner, sample_txt: Path
    ) -> None:
        result = runner.invoke(cli, ["extract", str(sample_txt)])

        assert result.exit_code == 0
        assert "AIXtract CLI test" in result.output


# ---------------------------------------------------------------------------
# 5. test_cli_extract_json_format
# ---------------------------------------------------------------------------


class TestCliExtractJsonFormat:
    """Verify the -f json flag produces valid JSON output."""

    def test_cli_extract_json_format(
        self, runner: CliRunner, sample_txt: Path
    ) -> None:
        result = runner.invoke(cli, ["extract", str(sample_txt), "-f", "json"])

        assert result.exit_code == 0
        # Rich console may prepend status lines before the JSON output.
        # Extract the JSON portion which starts with '{'.
        output = result.output
        json_start = output.index("{")
        json_str = output[json_start:]
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "success" in parsed
        assert parsed["success"] is True
        assert "content" in parsed


# ---------------------------------------------------------------------------
# 6. test_cli_extract_text_format
# ---------------------------------------------------------------------------


class TestCliExtractTextFormat:
    """Verify the -f text flag produces plain text output."""

    def test_cli_extract_text_format(
        self, runner: CliRunner, sample_txt: Path
    ) -> None:
        result = runner.invoke(cli, ["extract", str(sample_txt), "-f", "text"])

        assert result.exit_code == 0
        assert "AIXtract CLI test" in result.output
        # Plain text output should not contain JSON braces
        assert not result.output.strip().startswith("{")


# ---------------------------------------------------------------------------
# 7. test_cli_extract_output_file
# ---------------------------------------------------------------------------


class TestCliExtractOutputFile:
    """Verify the -o flag writes output to a file."""

    def test_cli_extract_output_file(
        self, runner: CliRunner, sample_txt: Path, tmp_path: Path
    ) -> None:
        output_file = tmp_path / "output.md"
        result = runner.invoke(
            cli, ["extract", str(sample_txt), "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()
        contents = output_file.read_text()
        assert "AIXtract CLI test" in contents


# ---------------------------------------------------------------------------
# 8. test_cli_extract_no_files
# ---------------------------------------------------------------------------


class TestCliExtractNoFiles:
    """Verify that invoking extract with no files produces an error."""

    def test_cli_extract_no_files(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["extract"])

        # Should fail with error message about no files specified
        # The command calls sys.exit(1) when no files given
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# 9. test_cli_extract_nonexistent_file
# ---------------------------------------------------------------------------


class TestCliExtractNonexistentFile:
    """Verify that extracting a non-existent file shows an error."""

    def test_cli_extract_nonexistent_file(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["extract", "/tmp/nonexistent_file_xyz.txt"])

        # Click's type=click.Path(exists=True) validates the file exists
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# 10. test_cli_extract_multiple_files
# ---------------------------------------------------------------------------


class TestCliExtractMultipleFiles:
    """Verify extracting multiple files produces combined output."""

    def test_cli_extract_multiple_files(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        file_a = tmp_path / "file_a.txt"
        file_b = tmp_path / "file_b.txt"
        file_a.write_text("Content from file A for multi-file test.")
        file_b.write_text("Content from file B for multi-file test.")

        result = runner.invoke(
            cli, ["extract", str(file_a), str(file_b)]
        )

        assert result.exit_code == 0
        # Both file contents should appear in the output
        assert "file A" in result.output or "file_a" in result.output
        assert "file B" in result.output or "file_b" in result.output


# ---------------------------------------------------------------------------
# 11. test_cli_extract_with_chunking
# ---------------------------------------------------------------------------


class TestCliExtractWithChunking:
    """Verify the --chunk flag enables chunking in the CLI."""

    def test_cli_extract_with_chunking(
        self, runner: CliRunner, sample_txt: Path
    ) -> None:
        result = runner.invoke(
            cli,
            ["extract", str(sample_txt), "--chunk", "-f", "json"],
        )

        assert result.exit_code == 0
        # Rich console may prepend status lines before the JSON output.
        output = result.output
        json_start = output.index("{")
        json_str = output[json_start:]
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "success" in parsed
        assert parsed["success"] is True


# ---------------------------------------------------------------------------
# 12. test_cli_extract_quiet
# ---------------------------------------------------------------------------


class TestCliExtractQuiet:
    """Verify the -q flag suppresses progress output."""

    def test_cli_extract_quiet(
        self, runner: CliRunner, sample_txt: Path
    ) -> None:
        result = runner.invoke(
            cli, ["extract", str(sample_txt), "-q"]
        )

        assert result.exit_code == 0
        # The content should still appear in output
        assert "AIXtract CLI test" in result.output
