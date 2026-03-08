from ytmusicapi import YTMusic
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize YouTube Music client
ytmusic = YTMusic("browser.json")

def get_ytmusic_playlist_tracks(playlist_id: str) -> list[str]:
    """
    Retrieve all tracks from a YouTube Music playlist.

    Args:
        playlist_id (str): The ID of the YouTube Music playlist.

    Returns:
        list[str]: A list of track queries in the format "Artist Title".
    """
    try:
        playlist = ytmusic.get_playlist(playlist_id)
        items = playlist.get("tracks", [])

        results = []
        for track in items:
            title = track.get("title", "Unknown Title")
            artists = track.get("artists", [])
            artist = artists[0]["name"] if artists else "Unknown Artist"

            full_query = f"{artist} {title}"
            results.append(full_query)

        logging.info(f"Retrieved {len(results)} tracks from playlist {playlist_id}.")
        return results
    except Exception as e:
        logging.error(f"Error retrieving tracks from playlist {playlist_id}: {e}")
        return []

def search_songs_ytmusic(songs_spotify: list[str]) -> list[str | None]:
    """
    Search for YouTube Music video IDs based on Spotify song queries.

    Args:
        songs_spotify (list[str]): List of song queries from Spotify.

    Returns:
        list[str | None]: List of YouTube Music video IDs or None if not found.
    """
    songs_ids = []

    for song in tqdm(songs_spotify, desc="Searching songs on YouTube Music"):
        try:
            results = ytmusic.search(song)

            video_id = None
            for item in results:
                if item.get("videoId"):
                    video_id = item["videoId"]
                    break

            if video_id is None:
                logging.warning(f"No video ID found for song: {song}")

            songs_ids.append(video_id)
        except Exception as e:
            logging.error(f"Error searching for song '{song}': {e}")
            songs_ids.append(None)

    logging.info(f"Completed search for {len(songs_spotify)} songs.")
    return songs_ids

def create_ytmusic_playlist(
    playlist_name: str,
    playlist_privacy: str = "PRIVATE",
    songs_id: list[str] | None = None
) -> str:
    """
    Create a new playlist on YouTube Music.

    Args:
        playlist_name (str): The name of the playlist.
        playlist_privacy (str): Privacy status, must be 'PUBLIC', 'PRIVATE', or 'UNLISTED'.
        songs_id (list[str] | None): List of video IDs to add to the playlist.

    Returns:
        str: Success or error message.
    """
    if not songs_id:
        return "No songs provided to create playlist."

    try:
        ytmusic.create_playlist(
            title=playlist_name,
            description="",
            privacy_status=playlist_privacy,
            video_ids=songs_id
        )
        logging.info(f"Playlist '{playlist_name}' created successfully.")
        return f"Playlist '{playlist_name}' was created!"
    except Exception as e:
        logging.exception(f"Error creating YouTube Music playlist '{playlist_name}': {e}")
        return f"Failed to create playlist '{playlist_name}': {e}"

def get_ytmusic_playlists() -> list[dict]:
    """
    Retrieve all library playlists from YouTube Music.

    Returns:
        list[dict]: A list of dictionaries with 'name' and 'id' keys.
    """
    try:
        playlists = ytmusic.get_library_playlists()
        result = []

        for playlist in playlists:
            name = playlist.get("title", "Unknown")
            playlist_id = playlist.get("playlistId")
            if playlist_id:
                result.append({
                    "name": name,
                    "id": playlist_id
                })

        logging.info(f"Retrieved {len(result)} playlists from YouTube Music library.")
        return result
    except Exception as e:
        logging.error(f"Error retrieving YouTube Music playlists: {e}")
        return []

def get_ytmusic_playlist_name(playlist_id: str) -> str:
    """
    Get the name of a YouTube Music playlist.

    Args:
        playlist_id (str): The ID of the playlist.

    Returns:
        str: The name of the playlist.
    """
    try:
        result = ytmusic.get_playlist(playlist_id)
        return result.get("title", "Unknown Playlist")
    except Exception as e:
        logging.error(f"Error retrieving playlist name for ID {playlist_id}: {e}")
        return "Unknown Playlist"

def delete_ytmusic_playlist(playlist_id: str) -> bool:
    """
    Delete a YouTube Music playlist.

    Args:
        playlist_id (str): The ID of the playlist to delete.

    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    try:
        ytmusic.delete_playlist(playlist_id)
        logging.info(f"Playlist {playlist_id} deleted successfully.")
        return True
    except Exception as e:
        logging.error(f"Error deleting playlist {playlist_id}: {e}")
        return False
