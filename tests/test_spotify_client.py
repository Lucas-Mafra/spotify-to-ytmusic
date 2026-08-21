"""Tests for the Spotify API client (with a fake spotipy backend)."""

from pathlib import Path
from typing import Any

import pytest

from spotify2yt.config import Settings
from spotify2yt.models import Track
from spotify2yt.spotify_client import SpotifyClient


class FakeSpotify:
    """Mimics the subset of spotipy.Spotify used by the client."""

    def __init__(self, pages: list[dict[str, Any]], playlist_name: str = "My Playlist"):
        self.pages = pages
        self.playlist_name = playlist_name
        self.calls: list[int] = []

    def playlist_items(self, url: str, limit: int, offset: int) -> dict[str, Any]:
        self.calls.append(offset)
        return self.pages[offset // limit]

    def playlist(self, url: str) -> dict[str, Any]:
        return {"name": self.playlist_name}

    def current_user(self) -> dict[str, Any]:
        return {"id": "user-1"}

    def user_playlists(self, user_id: str) -> dict[str, Any]:
        return {
            "items": [{"name": "Chill", "external_urls": {"spotify": "https://x/1"}}],
            "next": None,
        }


@pytest.fixture
def client_with(monkeypatch: pytest.MonkeyPatch):
    def _install(fake: FakeSpotify) -> SpotifyClient:
        settings = Settings(
            spotify_client_id="id",
            spotify_client_secret="secret",
            spotify_redirect_uri="http://localhost",
            ytmusic_auth_path=Path("browser.json"),
        )
        client = SpotifyClient(settings)
        monkeypatch.setattr(client, "_client", fake)
        return client

    return _install


class TestGetTracks:
    def test_parses_track_metadata(self, client_with) -> None:
        page = {
            "items": [
                {
                    "track": {
                        "name": "Bohemian Rhapsody",
                        "artists": [{"name": "Queen"}],
                        "album": {"name": "Opera"},
                        "duration_ms": 355_000,
                    }
                }
            ],
            "total": 1,
        }
        client = client_with(FakeSpotify([page]))

        tracks = client.get_tracks("url")

        assert tracks == [
            Track(
                artist="Queen",
                title="Bohemian Rhapsody",
                artists=("Queen",),
                album="Opera",
                duration_ms=355_000,
            )
        ]

    def test_skips_entries_without_track(self, client_with) -> None:
        page = {
            "items": [
                {"track": None},
                {"track": {"name": "Song", "artists": [{"name": "A"}]}},
            ],
            "total": 2,
        }
        client = client_with(FakeSpotify([page]))

        tracks = client.get_tracks("url")
        assert [track.title for track in tracks] == ["Song"]

    def test_paginates_beyond_first_page(self, client_with) -> None:
        first = {
            "items": [{"track": {"name": "S1", "artists": [{"name": "A"}]}}],
            "total": 101,
        }
        second = {
            "items": [{"track": {"name": "S2", "artists": [{"name": "A"}]}}],
            "total": 101,
        }
        fake = FakeSpotify([first, second])
        client = client_with(fake)

        tracks = client.get_tracks("url")

        assert [track.title for track in tracks] == ["S1", "S2"]
        assert fake.calls == [0, 100]


class TestGetPlaylists:
    def test_returns_name_and_link(self, client_with) -> None:
        client = client_with(FakeSpotify([]))

        playlists = client.get_playlists()

        assert [(p.name, p.link) for p in playlists] == [("Chill", "https://x/1")]


class TestGetPlaylistName:
    def test_returns_playlist_name(self, client_with) -> None:
        client = client_with(FakeSpotify([], playlist_name="Road Trip"))

        assert client.get_playlist_name("url") == "Road Trip"
