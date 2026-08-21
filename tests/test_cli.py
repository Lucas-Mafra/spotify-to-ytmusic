"""Tests for the CLI surface (no network access needed)."""

from pathlib import Path

from typer.testing import CliRunner

from spotify2yt.cli import app

runner = CliRunner()


class TestGlobalCommands:
    def test_version_reports_package_version(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.output.strip()

    def test_start_shows_command_overview(self, monkeypatch: object) -> None:
        result = runner.invoke(app, ["start"])
        assert result.exit_code == 0
        for command in ("spotify", "ytmusic", "transfer"):
            assert command in result.output

    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        assert "Usage" in result.output


class TestCacheCommand:
    def test_clear_cache_writes_empty_cache(self, tmp_path: Path) -> None:
        # chdir keeps the real cache.json in the repo untouched.
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)
            result = runner.invoke(app, ["clear-cache"])
        finally:
            os.chdir(original_cwd)

        assert result.exit_code == 0
        assert (tmp_path / "cache.json").exists()
