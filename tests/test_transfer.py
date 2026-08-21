"""Tests for the transfer orchestration."""

from pathlib import Path

import pytest

from spotify2yt.cache import Cache
from spotify2yt.models import Playlist, Track
from spotify2yt.transfer import TransferService


class FakeSpotify:
    def get_tracks(self, playlist_url: str) -> list[Track]:
        return [Track(artist="Artist", title="Song", duration_ms=1_000)]

    def get_playlist_name(self, playlist_url: str) -> str:
        return "Fetched Name"

    def get_playlists(self) -> list[Playlist]:
        return [Playlist(name="Fetched Name", link="url")]


class FakeYTMusic:
    def __init__(self) -> None:
        self.searched_with: list[Track] = []
        self.created: list[tuple[str, list[str], str]] = []

    def search_video_ids(self, tracks: list[Track]) -> list[str]:
        self.searched_with = list(tracks)
        return ["id1"]

    def create_playlist(self, name: str, video_ids: list[str], privacy: str) -> str:
        self.created.append((name, video_ids, privacy))
        return f"Playlist '{name}' was created!"


@pytest.fixture
def service(tmp_path: Path) -> tuple[TransferService, Cache, FakeYTMusic]:
    cache = Cache(path=tmp_path / "cache.json")
    ytmusic = FakeYTMusic()
    service = TransferService(
        spotify=FakeSpotify(),  # type: ignore[arg-type]
        ytmusic=ytmusic,  # type: ignore[arg-type]
        cache=cache,
    )
    return service, cache, ytmusic


class TestTransferSingle:
    def test_full_flow_uses_fetched_name_by_default(
        self, service: tuple[TransferService, Cache, FakeYTMusic]
    ) -> None:
        svc, _, ytmusic = service

        result = svc.transfer_single("url")

        assert result == "Playlist 'Fetched Name' was created!"
        assert ytmusic.created == [("Fetched Name", ["id1"], "PRIVATE")]

    def test_unmatched_tracks_are_dropped(
        self, service: tuple[TransferService, Cache, FakeYTMusic]
    ) -> None:
        svc, cache, _ = service

        svc.transfer_single("url")

        assert cache.ytmusic_songsid == ["id1"]

    def test_cache_is_cleared_before_import(
        self, service: tuple[TransferService, Cache, FakeYTMusic]
    ) -> None:
        svc, cache, ytmusic = service
        stale = Track(artist="Old", title="Stale")
        cache.spotify_tracks = [stale]
        cache.ytmusic_songsid = ["stale-id"]

        svc.transfer_single("url")

        assert ytmusic.searched_with and all(t.title != "Stale" for t in ytmusic.searched_with)
        assert [t.title for t in cache.spotify_tracks] == ["Song"]


class TestTransferAll:
    def test_transfers_every_playlist(
        self, service: tuple[TransferService, Cache, FakeYTMusic]
    ) -> None:
        svc, _, ytmusic = service

        count = svc.transfer_all()

        assert count == 1
        assert len(ytmusic.created) == 1
