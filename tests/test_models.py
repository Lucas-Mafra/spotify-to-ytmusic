from spotify2yt.models import Playlist, Track


class TestTrack:
    def test_query_joins_artist_and_title(self) -> None:
        assert Track(artist="Radiohead", title="Karma Police").query == "Radiohead Karma Police"

    def test_frozen(self) -> None:
        track = Track(artist="a", title="b")
        try:
            track.artist = "c"  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("Track should be immutable")


class TestPlaylist:
    def test_defaults(self) -> None:
        playlist = Playlist(name="My Mix")
        assert playlist.link == ""
        assert playlist.playlist_id == ""

    def test_fields(self) -> None:
        playlist = Playlist(name="My Mix", link="http://x", playlist_id="abc")
        assert playlist.link == "http://x"
        assert playlist.playlist_id == "abc"
