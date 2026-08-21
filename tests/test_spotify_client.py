"""Tests for the Spotify API client (with a fake spotipy backend)."""

import pytest

from spotify2yt import spotify_client
from spotify2yt.matching import Track


class FakeSpotify:
    """Mimics the subset of spotipy.Spotify used by the client."""

    def __init__(self, pages, playlist_name="My Playlist"):
        self.pages = pages
        self.playlist_name = playlist_name
        self.calls = []

    def playlist_items(self, url, limit, offset):
        self.calls.append(offset)
        return self.pages[offset // limit]

    def playlist(self, url):
        return {"name": self.playlist_name}

    def current_user(self):
        return {"id": "user-1"}

    def user_playlists(self, user_id):
        return {
            "items": [{"name": "Chill", "external_urls": {"spotify": "https://x/1"}}],
            "next": None,
        }


@pytest.fixture
def fake_spotify(monkeypatch):
    def _install(fake):
        monkeypatch.setattr(spotify_client, "_client", fake)
        monkeypatch.setattr(
            spotify_client, "_get_client", lambda: fake
        )
        return fake

    return _install


class TestGetSpotifyTracks:
    def test_parses_track_metadata(self, fake_spotify):
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
        fake_spotify(FakeSpotify([page]))

        tracks = spotify_client.get_spotify_tracks("url")

        assert tracks == [
            Track(
                title="Bohemian Rhapsody",
                artists=("Queen",),
                album="Opera",
                duration_ms=355_000,
            )
        ]

    def test_skips_entries_without_track(self, fake_spotify):
        page = {
            "items": [
                {"track": None},
                {"track": {"name": "Song", "artists": [{"name": "A"}]}},
            ],
            "total": 2,
        }
        fake_spotify(FakeSpotify([page]))

        tracks = spotify_client.get_spotify_tracks("url")
        assert [track.title for track in tracks] == ["Song"]

    def test_paginates_beyond_first_page(self, fake_spotify):
        first = {
            "items": [{"track": {"name": "S1", "artists": [{"name": "A"}]}}],
            "total": 101,
        }
        second = {
            "items": [{"track": {"name": "S2", "artists": [{"name": "A"}]}}],
            "total": 101,
        }
        fake = fake_spotify(FakeSpotify([first, second]))

        tracks = spotify_client.get_spotify_tracks("url")

        assert [track.title for track in tracks] == ["S1", "S2"]
        assert fake.calls == [0, 100]


class TestGetSpotifyPlaylists:
    def test_returns_name_and_link(self, fake_spotify):
        fake_spotify(FakeSpotify([]))

        playlists = spotify_client.get_spotify_playlists()

        assert playlists == [{"name": "Chill", "link": "https://x/1"}]


class TestSelectSpotifyPlaylist:
    def test_returns_playlist_name(self, fake_spotify):
        fake_spotify(FakeSpotify([], playlist_name="Road Trip"))

        assert spotify_client.select_spotify_playlist("url") == "Road Trip"
