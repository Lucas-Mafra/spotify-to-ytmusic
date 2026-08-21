"""Transfer orchestration between Spotify and YouTube Music."""

from __future__ import annotations

from . import ytmusic_client as ytm
from .cache import Cache
from .spotify_client import get_spotify_tracks, select_spotify_playlist


def transfer_spotify_playlist(
    cache: Cache,
    url: str,
    *,
    name: str | None = None,
    privacy: str = "PRIVATE",
) -> str:
    """Import a Spotify playlist, find its tracks and create a YouTube Music playlist.

    The cache is used as an intermediate store between the import, search and
    creation steps. It is reset at the start of every transfer so no stale data
    leaks in between runs.

    Args:
        cache: Shared cache instance used to persist intermediate state.
        url: Spotify playlist URL.
        name: Optional playlist name. If omitted it is fetched from Spotify.
        privacy: Privacy of the new YouTube Music playlist.

    Returns:
        Result message reported by ``create_ytmusic_playlist``.
    """
    cache.clear()
    playlist_name = name or select_spotify_playlist(url)

    cache.spotify_tracks = get_spotify_tracks(url)
    cache.save()

    cache.ytmusic_songsid = [
        song_id
        for song_id in ytm.search_songs_ytmusic(cache.spotify_tracks)
        if song_id is not None
    ]
    cache.save()

    return ytm.create_ytmusic_playlist(playlist_name, privacy, cache.ytmusic_songsid)
