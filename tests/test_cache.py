"""Tests for the local cache."""

import json

import pytest

from spotify2yt import cache as cache_module
from spotify2yt.cache import Cache
from spotify2yt.matching import Track


@pytest.fixture
def cache_file(tmp_path, monkeypatch):
    path = tmp_path / "cache.json"
    monkeypatch.setattr(cache_module, "CACHE_FILE", str(path))
    return path


class TestCache:
    def test_missing_file_starts_empty(self, cache_file):
        cache = Cache()
        assert cache.spotify_tracks == []
        assert cache.ytmusic_tracks == []
        assert cache.ytmusic_songsid == []

    def test_save_load_roundtrip(self, cache_file):
        track = Track(title="Song", artists=("Artist",), duration_ms=1_000)

        writer = Cache()
        writer.spotify_tracks = [track]
        writer.ytmusic_tracks = ["Artist Song"]
        writer.ytmusic_songsid = ["abc123"]
        writer.save()

        reader = Cache()
        assert reader.spotify_tracks == [track]
        assert reader.ytmusic_tracks == ["Artist Song"]
        assert reader.ytmusic_songsid == ["abc123"]

    def test_load_tolerates_legacy_string_entries(self, cache_file):
        legacy = {
            "spotify_tracks_cache": ["Queen Bohemian Rhapsody"],
            "ytmusic_tracks_cache": [],
            "ytmusic_songsid_cache": ["abc123"],
        }
        cache_file.write_text(json.dumps(legacy), encoding="utf-8")

        cache = Cache()
        assert cache.spotify_tracks == []
        assert cache.ytmusic_songsid == ["abc123"]

    def test_clear_resets_everything(self, cache_file):
        cache = Cache()
        cache.spotify_tracks = [Track(title="Song")]
        cache.ytmusic_songsid = ["abc123"]

        cache.clear()

        assert cache.spotify_tracks == []
        assert cache.ytmusic_songsid == []
        reloaded = Cache()
        assert reloaded.ytmusic_songsid == []
