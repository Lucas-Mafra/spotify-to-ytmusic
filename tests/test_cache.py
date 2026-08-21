"""Tests for the persistent cache."""

import json
from pathlib import Path

import pytest

from spotify2yt.cache import Cache
from spotify2yt.models import Track


@pytest.fixture
def cache_path(tmp_path: Path) -> Path:
    return tmp_path / "cache.json"


class TestCache:
    def test_missing_file_starts_empty(self, cache_path: Path) -> None:
        cache = Cache(path=cache_path)
        assert cache.spotify_tracks == []
        assert cache.ytmusic_tracks == []
        assert cache.ytmusic_songsid == []

    def test_save_load_roundtrip(self, cache_path: Path) -> None:
        track = Track(artist="Artist", title="Song", duration_ms=1_000)

        writer = Cache(path=cache_path)
        writer.spotify_tracks = [track]
        writer.ytmusic_tracks = ["Artist Song"]
        writer.ytmusic_songsid = ["abc123"]
        writer.save()

        reader = Cache(path=cache_path)
        assert reader.spotify_tracks == [track]
        assert reader.ytmusic_tracks == ["Artist Song"]
        assert reader.ytmusic_songsid == ["abc123"]

    def test_load_tolerates_legacy_string_entries(self, cache_path: Path) -> None:
        legacy = {
            "spotify_tracks_cache": ["Queen Bohemian Rhapsody"],
            "ytmusic_tracks_cache": [],
            "ytmusic_songsid_cache": ["abc123"],
        }
        cache_path.write_text(json.dumps(legacy), encoding="utf-8")

        cache = Cache(path=cache_path)
        assert cache.spotify_tracks == []
        assert cache.ytmusic_songsid == ["abc123"]

    def test_clear_resets_everything(self, cache_path: Path) -> None:
        cache = Cache(path=cache_path)
        cache.spotify_tracks = [Track(artist="A", title="S")]
        cache.ytmusic_songsid = ["abc123"]

        cache.clear()

        assert cache.spotify_tracks == []
        assert cache.ytmusic_songsid == []
        reloaded = Cache(path=cache_path)
        assert reloaded.ytmusic_songsid == []
