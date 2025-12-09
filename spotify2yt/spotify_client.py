import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="playlist-read-private"
    ))

def get_spotify_tracks(playlist_url: str):
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

        artist = track["artists"][0]["name"]
        name = track["name"]
        
        full_query = f"{artist} {name}"     
        tracks.append(full_query)

    return tracks

def get_spotify_playlists():
    try:
        playlists_page = sp.user_playlists(sp.current_user()['id'])
    except Exception as e:
        print("Error accessing user playlists:", e)
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

    return playlists

def select_spotify_playlist(url: str):
    return sp.playlist(url)["name"]
