"""Tests for the YouTube Music client (with a fake YTMusic backend)."""


import pytest

from spotify2yt import ytmusic_client as ytm
from spotify2yt.matching import Track


class FakeYTMusic:
    """Mimics the subset of ytmusicapi.YTMusic used by the client."""

    def __init__(self, search_results=None, playlists=None):
        self.search_results = search_results or {}
        self.playlists = playlists or []
        self.created = None

    def search(self, query, filter, limit):
        return self.search_results.get(filter, [])

    def get_library_playlists(self):
        return self.playlists

    def create_playlist(self, **kwargs):
        self.created = kwargs
        return "playlist-id"


@pytest.fixture
def fake_client(monkeypatch):
    def _install(fake):
        monkeypatch.setattr(ytm, "_client", fake)
        monkeypatch.setattr(ytm, "_get_client", lambda: fake)
        return fake

    return _install


TRACK = Track(
    title="Bohemian Rhapsody",
    artists=("Queen",),
    duration_ms=355_000,
)


class TestCandidateFields:
    def test_extracts_title_artists_and_duration(self):
        item = {
            "title": "Song",
            "artists": [{"name": "A"}, {"name": None}, "junk"],
            "duration_seconds": 200,
        }
        assert ytm._candidate_fields(item) == ("Song", ["A"], 200.0)

    def test_handles_missing_fields(self):
        assert ytm._candidate_fields({}) == ("", [], None)


class TestBestCandidate:
    def test_picks_highest_scoring_result(self):
        results = [
            {"videoId": "bad", "title": "Unrelated", "artists": [{"name": "X"}]},
            {
                "videoId": "good",
                "title": "Bohemian Rhapsody",
                "artists": [{"name": "Queen"}],
            },
        ]
        video_id, score = ytm._best_candidate(TRACK, results)
        assert video_id == "good"
        assert score > 0.8

    def test_skips_items_without_video_id(self):
        results = [{"title": "Bohemian Rhapsody", "artists": [{"name": "Queen"}]}]
        assert ytm._best_candidate(TRACK, results) == (None, 0.0)


class TestMatchTrack:
    def test_accepts_song_above_threshold(self, fake_client):
        fake_client(
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
        assert ytm._match_track(TRACK) == "song1"

    def test_falls_back_to_videos(self, fake_client):
        fake_client(
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
        assert ytm._match_track(TRACK) == "vid1"

    def test_returns_none_when_nothing_matches(self, fake_client):
        fake_client(FakeYTMusic({"songs": [], "videos": []}))
        assert ytm._match_track(TRACK) is None

    def test_survives_search_errors(self, fake_client):
        class ExplodingClient(FakeYTMusic):
            def search(self, query, filter, limit):
                raise RuntimeError("network down")

        fake_client(ExplodingClient())
        assert ytm._match_track(TRACK) is None


class TestSearchSongsYtmusic:
    def test_maps_every_track_in_order(self, fake_client, monkeypatch):
        fake_client(
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
        monkeypatch.setattr(
            "spotify2yt.ytmusic_client.tqdm", lambda items, desc="": items
        )

        other = Track(title="Totally Different", artists=("Zzz",))
        result = ytm.search_songs_ytmusic([TRACK, other])

        assert result == ["id1", None]


class TestCreatePlaylist:
    def test_rejects_empty_song_list(self, fake_client):
        message = ytm.create_ytmusic_playlist("Name", "PRIVATE", [])
        assert message == "No songs provided to create playlist."

    def test_creates_playlist_with_video_ids(self, fake_client):
        fake = fake_client(FakeYTMusic())

        message = ytm.create_ytmusic_playlist("Mix", "PUBLIC", ["a", "b"])

        assert message == "Playlist 'Mix' was created!"
        assert fake.created == {
            "title": "Mix",
            "description": "",
            "privacy_status": "PUBLIC",
            "video_ids": ["a", "b"],
        }


class TestGetPlaylists:
    def test_skips_entries_without_id(self, fake_client):
        fake_client(
            FakeYTMusic(
                playlists=[
                    {"playlistId": "p1", "title": "Chill"},
                    {"title": "No id"},
                ]
            )
        )

        assert ytm.get_ytmusic_playlists() == [{"name": "Chill", "id": "p1"}]


class TestAuthFile:
    def test_env_var_wins_when_file_exists(self, tmp_path, monkeypatch):
        auth = tmp_path / "custom.json"
        auth.write_text("{}")
        monkeypatch.setenv("YTMUSIC_AUTH_FILE", str(auth))
        assert ytm._auth_file() == str(auth)

    def test_env_var_missing_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.setenv("YTMUSIC_AUTH_FILE", str(tmp_path / "nope.json"))
        with pytest.raises(RuntimeError, match="auth file not found"):
            ytm._auth_file()

    def test_probes_default_files_in_order(self, tmp_path, monkeypatch):
        monkeypatch.delenv("YTMUSIC_AUTH_FILE", raising=False)
        monkeypatch.chdir(tmp_path)
        (tmp_path / "headers_auth.json").write_text("{}")

        assert ytm._auth_file() == "headers_auth.json"

    def test_raises_when_no_auth_file_exists(self, tmp_path, monkeypatch):
        monkeypatch.delenv("YTMUSIC_AUTH_FILE", raising=False)
        monkeypatch.chdir(tmp_path)
        with pytest.raises(RuntimeError, match="No YouTube Music auth file"):
            ytm._auth_file()


class TestOauthCredentials:
    def test_none_without_env_vars(self, monkeypatch):
        monkeypatch.delenv("YTMUSIC_CLIENT_ID", raising=False)
        monkeypatch.delenv("YTMUSIC_CLIENT_SECRET", raising=False)
        assert ytm._oauth_credentials() is None

    def test_partial_credentials_raise(self, monkeypatch):
        monkeypatch.setenv("YTMUSIC_CLIENT_ID", "id")
        monkeypatch.delenv("YTMUSIC_CLIENT_SECRET", raising=False)
        with pytest.raises(RuntimeError, match="both"):
            ytm._oauth_credentials()

    def test_builds_credentials_from_env(self, monkeypatch):
        monkeypatch.setenv("YTMUSIC_CLIENT_ID", "id")
        monkeypatch.setenv("YTMUSIC_CLIENT_SECRET", "secret")
        credentials = ytm._oauth_credentials()
        assert isinstance(credentials, ytm.OAuthCredentials)
