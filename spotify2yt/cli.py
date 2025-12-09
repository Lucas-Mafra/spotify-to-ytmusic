import typer
import logging
import json
import os
from rich import print
from .spotify_client import get_spotify_tracks, get_spotify_playlists, select_spotify_playlist
from . import ytmusic_client as ytm
app = typer.Typer()

CACHE_FILE = "cache.json"

# CACHE SYSTEM
def load_cache():
    global spotify_tracks_cache, ytmusic_tracks_cache, ytmusic_songsid_cache

    if not os.path.exists(CACHE_FILE):
        spotify_tracks_cache = []
        ytmusic_tracks_cache = []
        ytmusic_songsid_cache = []
        return

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    spotify_tracks_cache = data.get("spotify_tracks_cache", [])
    ytmusic_tracks_cache = data.get("ytmusic_tracks_cache", [])
    ytmusic_songsid_cache = data.get("ytmusic_songsid_cache", [])


def save_cache():
    data = {
        "spotify_tracks_cache": spotify_tracks_cache,
        "ytmusic_tracks_cache": ytmusic_tracks_cache,
        "ytmusic_songsid_cache": ytmusic_songsid_cache,
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# Load cache at startup
spotify_tracks_cache = []
ytmusic_tracks_cache = []
ytmusic_songsid_cache = []
spotify_playlist_count = 0
ytmusic_playlist_count = 0
load_cache()


# COMMANDS
@app.command()
def start():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("""[bold cyan] 
           Welcome!  
           For Ytmusic playlists, you only need the playlist ID (https://music.youtube.com/playlist?list={ID}), 
           and for Spotify, the full link works (https://open.spotify.com/...).
           [/bold cyan]
           [bold yellow]
           Commands:
                - import-spotify: url spotify
                - import-ytmusic: id ytmusic
                - getplaylists-spotify
                - getplaylists-ytmusic
                - searchsongs-ytmusic
                - create-ytmusic-playlist: playlist_name, privacy (optional, default value: PRIVATE)
                - transfer-all
                - fast-playlist: url spotify
                - clear-cache
           [/bold yellow]
           """)


@app.command("getplaylists-spotify")
def import_user_playlist_spotify():
    playlists = get_spotify_playlists()

    if not playlists:
        print("No playlists found.")
        return

    for p in playlists:
        print(f"{p['name']} - {p['link']}")


@app.command("getplaylists-ytmusic")
def import_user_playlist_ytmusic():
    playlists = ytm.get_ytmusic_playlists()

    if not playlists:
        print("No playlists found.")
        return

    for p in playlists:
        print(f"{p['name']} - {p['id']}")


@app.command("import-spotify")
def import_spotify(url: str):
    global spotify_tracks_cache

    print("[bold cyan]Fetching Spotify playlist...[/bold cyan]")
    try:
        spotify_tracks_cache = get_spotify_tracks(url)
        save_cache()
        print(f"[green]Imported {len(spotify_tracks_cache)} tracks from Spotify.[/green]")

    except Exception as e:
        logging.exception("Error catching Spotify playlist musics.")
        return f"Failed to get playlist music: {e}"


@app.command("import-ytmusic")
def import_ytmusic(id: str):
    global ytmusic_tracks_cache

    print("[bold cyan]Fetching Youtube Music playlist...[/bold cyan]")
    try:
        ytmusic_tracks_cache = ytm.get_ytmusic_playlist_tracks(id)
        save_cache()
        print(f"[green]Imported {len(ytmusic_tracks_cache)} tracks from YouTube Music.[/green]")
    
    except Exception as e:
        logging.exception("Error catching Spotify playlist musics.")
        return f"Failed to get playlist music: {e}"


@app.command("searchsongs-ytmusic")
def get_idsongs_ytmusic():
    global ytmusic_songsid_cache

    if not spotify_tracks_cache:
        print("[red]You need to import a playlist first: use 'import-spotify'.[/red]")
        return

    print("[cyan]Searching for IDs on YouTube Music...[/cyan]")
    ytmusic_songsid_cache = ytm.search_songs_ytmusic(spotify_tracks_cache)
    save_cache()

    print("[green]Number of tracks found:[/green]")
    print(len(ytmusic_songsid_cache))


@app.command("create-ytmusic-playlist")
def create_playlist_ytmusic(
    playlist_name: str = typer.Argument(...),
    privacy: str = typer.Option("PRIVATE", help="Playlist privacy: PRIVATE, PUBLIC, UNLISTED")
):
    if not ytmusic_songsid_cache:
        print("[red]No song IDs in cache. Run 'searchsongs-ytmusic' first.[/red]")
        return
    
    
    if privacy not in ("PRIVATE", "PUBLIC", "UNLISTED"):
        print("[red]The privacy parameter must be PRIVATE, PUBLIC, or UNLISTED.[/red]")
        return
    
    print("[cyan]Creating YouTube Music playlist...[/cyan]")
    result = ytm.create_ytmusic_playlist(playlist_name, privacy, ytmusic_songsid_cache)

    print(f'[green]{result}[/green]')


@app.command("transfer-all")
def transfer_all_playlist():
    clear_cache()
    
    playlists = get_spotify_playlists()

    try:
        for p in playlists:
            os.system('cls' if os.name == 'nt' else 'clear')

            name_playlist = p['name']
            playlist_link = p['link']

            print(f"[bold cyan]Transferring {name_playlist} playlist...[/bold cyan]")

            import_spotify(playlist_link)
            get_idsongs_ytmusic()
            create_playlist_ytmusic(name_playlist, privacy="PRIVATE")

        print(f'[green]Transfer sucessed![/green]')
    
    except Exception as e:
        logging.exception("Error transferring Spotify playlist to YouTube Music.")
        return f"Failed to trasnfer playlists: {e}"
    

@app.command("fast-playlist")
def fast_playlist_transfer(url: str):
    playlist_name = select_spotify_playlist(url)

    try:
        import_spotify(url)
        get_idsongs_ytmusic()
        create_playlist_ytmusic(playlist_name, privacy="PRIVATE")
    
    except Exception as e:
        logging.exception("Error creating Youtube Music playlist.")
        return f"Failed creating playlist: {e}"


@app.command("clear-cache")
def clear_cache():
    global spotify_tracks_cache, ytmusic_tracks_cache, ytmusic_songsid_cache

    spotify_tracks_cache = []
    ytmusic_tracks_cache = []
    ytmusic_songsid_cache = []

    save_cache()

    print("[green]Cache cleared![/green]")


def run():
    app()
