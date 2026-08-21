import json
import os

from .matching import Track

CACHE_FILE = "cache.json"


class Cache:
    """Simple container for cached track lists and helper methods.

    Having a dedicated class makes it easier to control file access when
    bundling the application into a single executable (e.g. with PyInstaller).
    Globals are avoided and the state is explicit which makes the code easier
    to test and refactor.
    """

    def __init__(self) -> None:
        self.spotify_tracks: list[Track] = []
        self.ytmusic_tracks: list[str] = []
        self.ytmusic_songsid: list[str] = []
        self.load()

    def load(self) -> None:
        if not os.path.exists(CACHE_FILE):
            return

        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)

        raw_tracks = data.get("spotify_tracks_cache", [])
        # Tolerate caches written by older versions that stored plain strings.
        self.spotify_tracks = [
            Track.from_dict(track) for track in raw_tracks if isinstance(track, dict)
        ]
        self.ytmusic_tracks = data.get("ytmusic_tracks_cache", [])
        self.ytmusic_songsid = data.get("ytmusic_songsid_cache", [])

    def save(self) -> None:
        data = {
            "spotify_tracks_cache": [track.to_dict() for track in self.spotify_tracks],
            "ytmusic_tracks_cache": self.ytmusic_tracks,
            "ytmusic_songsid_cache": self.ytmusic_songsid,
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def clear(self) -> None:
        self.spotify_tracks = []
        self.ytmusic_tracks = []
        self.ytmusic_songsid = []
        self.save()
