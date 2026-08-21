from pathlib import Path

from spotify2yt.cache import Cache


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    cache = Cache(path)
    cache.spotify_tracks = ["Artist One", "Artist Two"]
    cache.ytmusic_tracks = ["Artist Three"]
    cache.ytmusic_songsid = ["vid-1", "vid-2"]
    cache.save()

    loaded = Cache(path)
    assert loaded.spotify_tracks == ["Artist One", "Artist Two"]
    assert loaded.ytmusic_tracks == ["Artist Three"]
    assert loaded.ytmusic_songsid == ["vid-1", "vid-2"]


def test_load_missing_file_keeps_defaults(tmp_path: Path) -> None:
    cache = Cache(tmp_path / "does-not-exist.json")
    assert cache.spotify_tracks == []
    assert cache.ytmusic_tracks == []
    assert cache.ytmusic_songsid == []


def test_clear_resets_state(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    cache = Cache(path)
    cache.spotify_tracks = ["Artist One"]
    cache.ytmusic_songsid = ["vid-1"]
    cache.save()

    cache.clear()

    assert cache.spotify_tracks == []
    assert cache.ytmusic_tracks == []
    assert cache.ytmusic_songsid == []
    assert Cache(path).spotify_tracks == []
