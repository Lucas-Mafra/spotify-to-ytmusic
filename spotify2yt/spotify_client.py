import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="playlist-read-private"
))

def get_spotify_tracks(playlist_url: str) -> list[str]:
    """
    Retrieve all tracks from a Spotify playlist.

    Args:
        playlist_url (str): The URL of the Spotify playlist.

    Returns:
        list[str]: A list of track queries in the format "Artist Name".
    """
    try:
        results = sp.playlist_items(playlist_url, limit=100, offset=0)
        items = results["items"]
        total = results["total"]

        offset = 100
        while offset < total:
            page = sp.playlist_items(playlist_url, limit=100, offset=offset)
            items.extend(page["items"])
            offset += 100

        tracks = []
        for item in items:
            track = item.get("track")
            if not track:
                continue

            artists = track.get("artists", [])
            if not artists:
                continue
            artist = artists[0]["name"]
            name = track["name"]

            full_query = f"{artist} {name}"
            tracks.append(full_query)

        logging.info(f"Retrieved {len(tracks)} tracks from playlist.")
        return tracks
    except Exception as e:
        logging.error(f"Error retrieving tracks from playlist {playlist_url}: {e}")
        return []

def get_spotify_playlists() -> list[dict]:
    """
    Retrieve all user playlists from Spotify.

    Returns:
        list[dict]: A list of dictionaries with 'name' and 'link' keys.
    """
    try:
        playlists_page = sp.user_playlists(sp.current_user()['id'])
    except Exception as e:
        logging.error(f"Error accessing user playlists: {e}")
        return []

    playlists = []

    while playlists_page:
        for playlist in playlists_page.get("items", []):
            playlists.append({
                "name": playlist.get("name", "No name"),
                "link": playlist.get("external_urls", {}).get("spotify", "")
            })

        next_page = playlists_page.get("next")
        playlists_page = sp.next(playlists_page) if next_page else None

    logging.info(f"Retrieved {len(playlists)} playlists.")
    return playlists

def select_spotify_playlist(url: str) -> str:
    """
    Get the name of a Spotify playlist from its URL.

    Args:
        url (str): The URL of the Spotify playlist.

    Returns:
        str: The name of the playlist.
    """
    try:
        playlist = sp.playlist(url)
        return playlist["name"]
    except Exception as e:
        logging.error(f"Error retrieving playlist name for URL {url}: {e}")
        return "Unknown Playlist"
