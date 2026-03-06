import logging
import os
import sys

import typer
from rich import print

from . import ytmusic_client as ytm
from .spotify_client import (
    get_spotify_playlists,
    get_spotify_tracks,
    select_spotify_playlist,
)

app = typer.Typer()
spotify_app = typer.Typer(help="Spotify-related commands")
ytmusic_app = typer.Typer(help="YouTube Music-related commands")
transfer_app = typer.Typer(help="Transfer playlists between services")

app.add_typer(spotify_app, name="spotify")
app.add_typer(ytmusic_app, name="ytmusic")
app.add_typer(transfer_app, name="transfer")

from .cache import Cache

# one shared cache instance used by all commands.  Using a class
# rather than module-level globals makes it easier to bundle the app and
# also makes testing simpler.
cache = Cache()


# START COMMAND
@app.command()
def start():
    os.system("cls" if os.name == "nt" else "clear")
    print("""[bold cyan]
           Welcome!
           For Ytmusic playlists, you only need the playlist ID (https://music.youtube.com/playlist?list={ID}),
           and for Spotify, the full link works (https://open.spotify.com/...).
           [/bold cyan]
           [bold yellow]
           Available Commands:
           
           Spotify:
                - spotify playlists          (get Spotify playlists)
                - spotify import URL         (import playlist from Spotify)
           
           YouTube Music:
                - ytmusic playlists          (get YouTube Music playlists)
                - ytmusic import ID          (import playlist from YouTube Music)
                - ytmusic search             (search songs on YouTube Music)
                - ytmusic create NAME        (create playlist on YouTube Music)
           
           Transfer:
                - transfer all               (transfer all Spotify playlists)
                - transfer quick URL         (transfer single Spotify playlist)
           
           Utility:
                - clear-cache                (clear all cached data)
           [/bold yellow]
           """)


# SPOTIFY COMMANDS
@spotify_app.command("playlists")
def import_user_playlist_spotify():
    playlists = get_spotify_playlists()

    if not playlists:
        print("No playlists found.")
        return

    for p in playlists:
        print(f"{p['name']} - {p['link']}")


@spotify_app.command("import")
def import_spotify(url: str):
    """Fetch songs from a Spotify playlist and persist them in the cache."""
    print("[bold cyan]Fetching Spotify playlist...[/bold cyan]")
    try:
        cache.spotify_tracks = get_spotify_tracks(url)
        cache.save()
        print(
            f"[green]Imported {len(cache.spotify_tracks)} tracks from Spotify.[/green]"
        )

    except Exception as e:
        logging.exception("Error catching Spotify playlist musics.")
        return f"Failed to get playlist music: {e}"


# YOUTUBE MUSIC COMMANDS
@ytmusic_app.command("playlists")
def import_user_playlist_ytmusic():
    playlists = ytm.get_ytmusic_playlists()

    if not playlists:
        print("No playlists found.")
        return

    for p in playlists:
        print(f"{p['name']} - {p['id']}")


@ytmusic_app.command("import")
def import_ytmusic(id: str):
    print("[bold cyan]Fetching Youtube Music playlist...[/bold cyan]")
    try:
        cache.ytmusic_tracks = ytm.get_ytmusic_playlist_tracks(id)
        cache.save()
        print(
            f"[green]Imported {len(cache.ytmusic_tracks)} tracks from YouTube Music.[/green]"
        )

    except Exception as e:
        logging.exception("Error catching Spotify playlist musics.")
        return f"Failed to get playlist music: {e}"


@ytmusic_app.command("search")
def get_idsongs_ytmusic():
    if not cache.spotify_tracks:
        print("[red]You need to import a playlist first: use 'spotify import'.[/red]")
        return

    print("[cyan]Searching for IDs on YouTube Music...[/cyan]")
    cache.ytmusic_songsid = ytm.search_songs_ytmusic(cache.spotify_tracks)
    cache.save()

    print("[green]Number of tracks found:[/green]")
    print(len(cache.ytmusic_songsid))


@ytmusic_app.command("create")
def create_playlist_ytmusic(
    playlist_name: str = typer.Argument(...),
    privacy: str = typer.Option(
        "PRIVATE", help="Playlist privacy: PRIVATE, PUBLIC, UNLISTED"
    ),
):
    if not cache.ytmusic_songsid:
        print("[red]No song IDs in cache. Run 'ytmusic search' first.[/red]")
        return

    if privacy not in ("PRIVATE", "PUBLIC", "UNLISTED"):
        print("[red]The privacy parameter must be PRIVATE, PUBLIC, or UNLISTED.[/red]")
        return

    print("[cyan]Creating YouTube Music playlist...[/cyan]")
    result = ytm.create_ytmusic_playlist(playlist_name, privacy, cache.ytmusic_songsid)

    print(f"[green]{result}[/green]")


# TRANSFER COMMANDS
@transfer_app.command("all")
def transfer_all_playlist():
    # use cache.clear() rather than the previous function so state is
    # reset consistently and saved.
    cache.clear()

    playlists = get_spotify_playlists()

    try:
        for p in playlists:
            os.system("cls" if os.name == "nt" else "clear")

            name_playlist = p["name"]
            playlist_link = p["link"]

            print(f"[bold cyan]Transferring {name_playlist} playlist...[/bold cyan]")

            import_spotify(playlist_link)
            get_idsongs_ytmusic()
            create_playlist_ytmusic(name_playlist, privacy="PRIVATE")

        print(f"[green]Transfer sucessed![/green]")

    except Exception as e:
        logging.exception("Error transferring Spotify playlist to YouTube Music.")
        return f"Failed to trasnfer playlists: {e}"


@transfer_app.command("quick")
def fast_playlist_transfer(url: str):
    playlist_name = select_spotify_playlist(url)

    try:
        import_spotify(url)
        get_idsongs_ytmusic()
        create_playlist_ytmusic(playlist_name, privacy="PRIVATE")

    except Exception as e:
        logging.exception("Error creating Youtube Music playlist.")
        return f"Failed creating playlist: {e}"


# UTILITY COMMANDS
@app.command("clear-cache")
def clear_cache():
    cache.clear()
    print("[green]Cache cleared![/green]")


def main():
    """Entry point used by console script or ``python -m spotify2yt``.

    When the project is frozen to a Windows executable with PyInstaller the
    cache file and data files will be located relative to ``sys._MEIPASS``
    so we adjust the current working directory if necessary before running
    the Typer app.
    """

    # on Windows builds PyInstaller extracts into a temporary folder; change
    # to that directory so relative paths continue to work.
    if getattr(sys, "frozen", False):
        os.chdir(sys._MEIPASS)

    app()


if __name__ == "__main__":
    main()
