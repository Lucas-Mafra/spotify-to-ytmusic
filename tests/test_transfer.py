"""Tests for the transfer orchestration."""

import pytest

from spotify2yt import transfer as transfer_module
from spotify2yt.cache import Cache
from spotify2yt.matching import Track


@pytest.fixture
def cache(tmp_path, monkeypatch):
    from spotify2yt import cache as cache_module

    monkeypatch.setattr(cache_module, "CACHE_FILE", str(tmp_path / "cache.json"))
    return Cache()


@pytest.fixture
def mocks(monkeypatch):
    calls = {"cleared": 0, "created": []}

    monkeypatch.setattr(
        transfer_module,
        "get_spotify_tracks",
        lambda url: [Track(title="Song", artists=("Artist",))],
    )
    monkeypatch.setattr(
        transfer_module, "select_spotify_playlist", lambda url: "Fetched Name"
    )
    monkeypatch.setattr(
        transfer_module.ytm,
        "search_songs_ytmusic",
        lambda tracks: ["id1", None],
    )

    def fake_create(name, privacy, song_ids):
        calls["created"].append((name, privacy, list(song_ids)))
        return f"Playlist '{name}' was created!"

    monkeypatch.setattr(transfer_module.ytm, "create_ytmusic_playlist", fake_create)

    original_clear = Cache.clear

    def counting_clear(self):
        calls["cleared"] += 1
        original_clear(self)

    monkeypatch.setattr(Cache, "clear", counting_clear)
    return calls


class TestTransferSpotifyPlaylist:
    def test_full_flow_uses_fetched_name_by_default(self, cache, mocks):
        result = transfer_module.transfer_spotify_playlist(cache, "url")

        assert result == "Playlist 'Fetched Name' was created!"
        assert mocks["created"] == [("Fetched Name", "PRIVATE", ["id1"])]

    def test_explicit_name_and_privacy_win(self, cache, mocks):
        transfer_module.transfer_spotify_playlist(
            cache, "url", name="Given", privacy="PUBLIC"
        )
        assert mocks["created"] == [("Given", "PUBLIC", ["id1"])]

    def test_unmatched_tracks_are_dropped(self, cache, mocks):
        transfer_module.transfer_spotify_playlist(cache, "url")
        assert cache.ytmusic_songsid == ["id1"]

    def test_cache_is_cleared_before_import(self, cache, mocks):
        cache.ytmusic_songsid = ["stale-id"]
        cache.spotify_tracks = [Track(title="Old")]

        transfer_module.transfer_spotify_playlist(cache, "url")

        assert mocks["cleared"] >= 1
        assert [track.title for track in cache.spotify_tracks] == ["Song"]
