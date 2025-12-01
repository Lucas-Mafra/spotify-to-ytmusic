from ytmusicapi import YTMusic
from tqdm import tqdm
import logging

ytmusic = YTMusic("browser.json")

def get_ytmusic_playlist_tracks(playlist_id: str):    
    playlist = ytmusic.get_playlist(playlist_id)
    items = playlist.get("tracks", [])

    results = []
    for t in items:
        title = t.get("title")
        artists = t.get("artists", [])
        artist = artists[0]["name"] if artists else "Unknown"

        full_query = f"{artist} {title}"
        results.append(full_query)

    return results

def search_songs_ytmusic(songs_spotify: list):
    songs_ids = []

    for song in tqdm(songs_spotify):
        results = ytmusic.search(song)

        video_id = None
        for item in results:
            if item.get("videoId"):
                video_id = item["videoId"]
                break

        songs_ids.append(video_id)

    return songs_ids

def create_ytmusic_playlist(
    playlist_name: str,
    playlist_privacy: str = "PRIVATE",
    songs_id: list = None
):
    """
    :param playlist_privacy: The values must be PUBLIC, PRIVATE, or UNLISTED.
    """
    if songs_id is None:
        songs_id = []
        return
    
    try:
        ytmusic.create_playlist(
            title=playlist_name,
            description="",
            privacy_status=playlist_privacy,
            video_ids=songs_id
        )
        return f'Playlist {playlist_name} was created !'

    except Exception as e:
        logging.exception("Error creating YouTube Music playlist")
        return f"Failed to create playlist '{playlist_name}': {e}"


def get_ytmusic_playlists():
    playlists = ytmusic.get_library_playlists()
    result = []

    for p in playlists:
        name = p.get("title")
        playlist_id = p.get("playlistId")
        
        result.append({
            "name": name,
            "id": playlist_id
        })

    return result

