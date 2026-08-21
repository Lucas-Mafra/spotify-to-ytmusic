"""Tests for the CLI surface (no network access needed)."""

from typer.testing import CliRunner

from spotify2yt import __version__
from spotify2yt.cli import app

runner = CliRunner()


class TestGlobalCommands:
    def test_version_reports_package_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_start_shows_command_overview(self):
        result = runner.invoke(app, ["start"])
        assert result.exit_code == 0
        for command in ("spotify", "ytmusic", "transfer", "cache"):
            assert command in result.output

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        assert "Usage" in result.output


class TestCacheCommands:
    def test_cache_show_renders_table(self, tmp_path, monkeypatch):
        from spotify2yt import cache as cache_module
        from spotify2yt.cli import cache as cli_cache

        monkeypatch.setattr(cache_module, "CACHE_FILE", str(tmp_path / "cache.json"))
        cli_cache.spotify_tracks.clear()
        cli_cache.ytmusic_songsid.clear()

        result = runner.invoke(app, ["cache", "show"])

        assert result.exit_code == 0
        assert "Spotify tracks" in result.output
