"""High-level orchestration for playlist transfers."""

from __future__ import annotations

import logging

from .cache import Cache
from .spotify_client import SpotifyClient
from .ytmusic_client import YouTubeMusicClient

logger = logging.getLogger(__name__)


class TransferService:
    """Coordinates Spotify and YouTube Music clients plus the session cache."""

    def __init__(
        self,
        spotify: SpotifyClient,
        ytmusic: YouTubeMusicClient,
        cache: Cache,
    ) -> None:
        self.spotify = spotify
        self.ytmusic = ytmusic
        self.cache = cache

    def import_spotify(self, playlist_url: str) -> int:
        """Fetch a Spotify playlist into the cache and return the track count."""
        tracks = self.spotify.get_tracks(playlist_url)
        self.cache.spotify_tracks = [t.query for t in tracks]
        self.cache.save()
        logger.info("Imported %d tracks from Spotify.", len(tracks))
        return len(tracks)

    def import_ytmusic(self, playlist_id: str) -> int:
        """Fetch a YouTube Music playlist into the cache and return the count."""
        tracks = self.ytmusic.get_playlist_tracks(playlist_id)
        self.cache.ytmusic_tracks = [t.query for t in tracks]
        self.cache.save()
        logger.info("Imported %d tracks from YouTube Music.", len(tracks))
        return len(tracks)

    def resolve_video_ids(self) -> int:
        """Resolve YouTube Music IDs for cached Spotify track queries."""
        self.cache.ytmusic_songsid = self.ytmusic.search_video_ids(self.cache.spotify_tracks)
        self.cache.save()
        return len(self.cache.ytmusic_songsid)

    def create_ytmusic_playlist(self, name: str, privacy: str = "PRIVATE") -> str:
        """Create a playlist from the cached video IDs and return a message."""
        return self.ytmusic.create_playlist(name, self.cache.ytmusic_songsid, privacy)

    def transfer_single(self, playlist_url: str) -> str:
        """Transfer a single Spotify playlist to YouTube Music end to end."""
        self.cache.clear()
        name = self.spotify.get_playlist_name(playlist_url)
        self.import_spotify(playlist_url)
        self.resolve_video_ids()
        return self.create_ytmusic_playlist(name)

    def transfer_all(self) -> int:
        """Transfer every Spotify playlist, returning how many were created."""
        transferred = 0
        for playlist in self.spotify.get_playlists():
            if not playlist.link:
                continue
            self.transfer_single(playlist.link)
            transferred += 1
        return transferred
