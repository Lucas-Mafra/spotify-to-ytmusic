"""Tests for the YouTube Music client (with a fake YTMusic backend)."""

from pathlib import Path
from typing import Any

import pytest

from spotify2yt.config import Settings
from spotify2yt.models import Track
from spotify2yt.ytmusic_client import YouTubeMusicClient

TRACK = Track(
    artist="Queen",
    title="Bohemian Rhapsody",
    artists=("Queen",),
    duration_ms=355_000,
)


class FakeYTMusic:
    """Mimics the subset of ytmusicapi.YTMusic used by the client."""

    def __init__(
        self,
        search_results: dict[str, list[dict[str, Any]]] | None = None,
        playlists: list[dict[str, Any]] | None = None,
    ):
        self.search_results = search_results or {}
        self.playlists = playlists or []
        self.created: dict[str, Any] | None = None

    def search(self, query: str, filter: str, limit: int) -> list[dict[str, Any]]:
        return self.search_results.get(filter, [])

    def get_library_playlists(self) -> list[dict[str, Any]]:
        return self.playlists

    def create_playlist(self, **kwargs: Any) -> str:
        self.created = kwargs
        return "playlist-id"


@pytest.fixture
def client_with(monkeypatch: pytest.MonkeyPatch):
    def _install(fake: FakeYTMusic) -> YouTubeMusicClient:
        settings = Settings(
            spotify_client_id="id",
            spotify_client_secret="secret",
            spotify_redirect_uri="http://localhost",
            ytmusic_auth_path=Path("browser.json"),
        )
        client = YouTubeMusicClient(settings)
        monkeypatch.setattr(client, "_client", fake)
        return client

    return _install


class TestBestCandidate:
    def test_picks_highest_scoring_result(self, client_with) -> None:
        results = [
            {"videoId": "bad", "title": "Unrelated", "artists": [{"name": "X"}]},
            {
                "videoId": "good",
                "title": "Bohemian Rhapsody",
                "artists": [{"name": "Queen"}],
            },
        ]
        client = client_with(FakeYTMusic())

        video_id, score = client._best_candidate(TRACK, results)

        assert video_id == "good"
        assert score > 0.8

    def test_skips_items_without_video_id(self, client_with) -> None:
        results = [{"title": "Bohemian Rhapsody", "artists": [{"name": "Queen"}]}]
        client = client_with(FakeYTMusic())

        assert client._best_candidate(TRACK, results) == (None, 0.0)


class TestMatchTrack:
    def test_accepts_song_above_threshold(self, client_with) -> None:
        client = client_with(
            FakeYTMusic(
                {
                    "songs": [
                        {
                            "videoId": "song1",
                            "title": "Bohemian Rhapsody",
                            "artists": [{"name": "Queen"}],
                            "duration_seconds": 355,
                        }
                    ]
                }
            )
        )

        assert client._match_track(TRACK) == "song1"

    def test_falls_back_to_videos(self, client_with) -> None:
        client = client_with(
            FakeYTMusic(
                {
                    "videos": [
                        {
                            "videoId": "vid1",
                            "title": "Bohemian Rhapsody",
                            "artists": [{"name": "Queen"}],
                            "duration_seconds": 355,
                        }
                    ]
                }
            )
        )

        assert client._match_track(TRACK) == "vid1"

    def test_returns_none_when_nothing_matches(self, client_with) -> None:
        client = client_with(FakeYTMusic({"songs": [], "videos": []}))

        assert client._match_track(TRACK) is None

    def test_survives_search_errors(self, client_with) -> None:
        class ExplodingClient(FakeYTMusic):
            def search(self, query: str, filter: str, limit: int):
                raise RuntimeError("network down")

        client = client_with(ExplodingClient())

        assert client._match_track(TRACK) is None


class TestSearchVideoIds:
    def test_maps_every_track_in_order(self, client_with) -> None:
        client = client_with(
            FakeYTMusic(
                {
                    "songs": [
                        {
                            "videoId": "id1",
                            "title": "Bohemian Rhapsody",
                            "artists": [{"name": "Queen"}],
                        }
                    ]
                }
            )
        )
        other = Track(artist="Zzz", title="Totally Different")

        result = client.search_video_ids([TRACK, other])

        assert result == ["id1"]


class TestCreatePlaylist:
    def test_rejects_empty_song_list(self, client_with) -> None:
        client = client_with(FakeYTMusic())

        message = client.create_playlist("Name", [])

        assert message == "No songs provided to create playlist."

    def test_creates_playlist_with_video_ids(self, client_with) -> None:
        fake = FakeYTMusic()
        client = client_with(fake)

        message = client.create_playlist("Mix", ["a", "b"], privacy="PUBLIC")

        assert message == "Playlist 'Mix' was created!"
        assert fake.created == {
            "title": "Mix",
            "description": "",
            "privacy_status": "PUBLIC",
            "video_ids": ["a", "b"],
        }


class TestGetPlaylists:
    def test_skips_entries_without_id(self, client_with) -> None:
        client = client_with(
            FakeYTMusic(
                playlists=[
                    {"playlistId": "p1", "title": "Chill"},
                    {"title": "No id"},
                ]
            )
        )

        playlists = client.get_playlists()

        assert [(p.name, p.playlist_id) for p in playlists] == [("Chill", "p1")]
