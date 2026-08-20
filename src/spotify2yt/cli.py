"""Typer CLI entry point for spotify2yt."""

from __future__ import annotations

import os
from typing import Annotated

import typer
from rich.console import Console

from .cache import Cache
from .config import Settings
from .logging import configure_logging
from .spotify_client import SpotifyClient
from .transfer import TransferService
from .ytmusic_client import YouTubeMusicClient

console = Console()

app = typer.Typer(help="Migrate playlists between Spotify and YouTube Music.", no_args_is_help=True)
spotify_app = typer.Typer(help="Spotify-related commands.", no_args_is_help=True)
ytmusic_app = typer.Typer(help="YouTube Music-related commands.", no_args_is_help=True)
transfer_app = typer.Typer(help="Transfer playlists between services.", no_args_is_help=True)

app.add_typer(spotify_app, name="spotify")
app.add_typer(ytmusic_app, name="ytmusic")
app.add_typer(transfer_app, name="transfer")


def _service() -> TransferService:
    """Build a fully-wired transfer service with lazily-initialized clients."""
    settings = Settings.from_env()
    return TransferService(
        spotify=SpotifyClient(settings),
        ytmusic=YouTubeMusicClient(settings),
        cache=Cache(),
    )


@app.callback(invoke_without_command=True)
def _root(
    show_version: Annotated[
        bool, typer.Option("--version", help="Show the version and exit.")
    ] = False,
) -> None:
    if show_version:
        from importlib.metadata import PackageNotFoundError, version

        try:
            console.print(version("spotify2yt"))
        except PackageNotFoundError:
            console.print("unknown")
        raise typer.Exit()


@app.command()
def start() -> None:
    """Show the welcome screen with available commands."""
    os.system("cls" if os.name == "nt" else "clear")
    console.print(
        """[bold cyan]
        Welcome!
        For YTMusic playlists, you only need the playlist ID
        (https://music.youtube.com/playlist?list={ID}),
        and for Spotify, the full link works
        (https://open.spotify.com/...).

        [bold yellow]Available Commands:[/bold yellow]

        Spotify:
            - spotify playlists      (get Spotify playlists)
            - spotify import URL     (import playlist from Spotify)

        YouTube Music:
            - ytmusic playlists      (get YouTube Music playlists)
            - ytmusic import ID      (import playlist from YouTube Music)
            - ytmusic search         (search songs on YouTube Music)
            - ytmusic create NAME    (create playlist on YouTube Music)
            - ytmusic check          (test the YouTube Music connection)

        Transfer:
            - transfer all           (transfer all Spotify playlists)
            - transfer quick URL     (transfer single Spotify playlist)

        Utility:
            - clear-cache            (clear all cached data)
        [/bold yellow]
        """
    )


# --- Spotify commands ---


@spotify_app.command("playlists")
def spotify_playlists() -> None:
    """List your Spotify playlists."""
    playlists = _service().spotify.get_playlists()
    for playlist in playlists:
        console.print(f"{playlist.name} - {playlist.link}")


@spotify_app.command("import")
def spotify_import(url: str) -> None:
    """Fetch songs from a Spotify playlist and persist them in the cache."""
    console.print("[bold cyan]Fetching Spotify playlist...[/bold cyan]")
    count = _service().import_spotify(url)
    console.print(f"[green]Imported {count} tracks from Spotify.[/green]")


# --- YouTube Music commands ---


@ytmusic_app.command("playlists")
def ytmusic_playlists() -> None:
    """List your YouTube Music playlists."""
    playlists = _service().ytmusic.get_playlists()
    for playlist in playlists:
        console.print(f"{playlist.name} - {playlist.playlist_id}")


@ytmusic_app.command("import")
def ytmusic_import(playlist_id: str) -> None:
    """Fetch songs from a YouTube Music playlist and persist them in the cache."""
    console.print("[bold cyan]Fetching YouTube Music playlist...[/bold cyan]")
    count = _service().import_ytmusic(playlist_id)
    console.print(f"[green]Imported {count} tracks from YouTube Music.[/green]")


@ytmusic_app.command("search")
def ytmusic_search() -> None:
    """Search for imported Spotify tracks on YouTube Music."""
    service = _service()
    if not service.cache.spotify_tracks:
        console.print("[red]You need to import a playlist first: use 'spotify import'.[/red]")
        raise typer.Exit(code=1)

    console.print("[cyan]Searching for IDs on YouTube Music...[/cyan]")
    found = service.resolve_video_ids()
    console.print(f"[green]Tracks found: {found}[/green]")


@ytmusic_app.command("create")
def ytmusic_create(
    playlist_name: str,
    privacy: Annotated[
        str, typer.Option(help="Playlist privacy: PRIVATE, PUBLIC, UNLISTED")
    ] = "PRIVATE",
) -> None:
    """Create a new YouTube Music playlist from the cached song IDs."""
    if privacy not in ("PRIVATE", "PUBLIC", "UNLISTED"):
        console.print("[red]The privacy parameter must be PRIVATE, PUBLIC, or UNLISTED.[/red]")
        raise typer.Exit(code=1)

    service = _service()
    if not service.cache.ytmusic_songsid:
        console.print("[red]No song IDs in cache. Run 'ytmusic search' first.[/red]")
        raise typer.Exit(code=1)

    console.print("[cyan]Creating YouTube Music playlist...[/cyan]")
    message = service.create_ytmusic_playlist(playlist_name, privacy)
    console.print(f"[green]{message}[/green]")


@ytmusic_app.command("check")
def ytmusic_check() -> None:
    """Test the YouTube Music connection using the configured auth file."""
    info = _service().ytmusic.account_info()
    console.print(info)


# --- Transfer commands ---


@transfer_app.command("all")
def transfer_all() -> None:
    """Transfer all your Spotify playlists to YouTube Music."""
    transferred = _service().transfer_all()
    console.print(f"[green]Transfer completed: {transferred} playlist(s).[/green]")


@transfer_app.command("quick")
def transfer_quick(url: str) -> None:
    """Quickly transfer a single Spotify playlist."""
    message = _service().transfer_single(url)
    console.print(f"[green]{message}[/green]")


# --- Utility commands ---


@app.command("clear-cache")
def clear_cache() -> None:
    """Clear all cached data."""
    Cache().clear()
    console.print("[green]Cache cleared![/green]")


def main() -> None:
    """Entry point used by the ``spotify2yt`` console script or ``python -m spotify2yt``."""
    configure_logging()
    app()
