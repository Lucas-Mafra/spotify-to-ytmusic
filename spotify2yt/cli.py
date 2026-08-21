"""Command-line interface for spotify2yt."""

from __future__ import annotations

import logging
import os
import sys

import typer
from pyfiglet import Figlet
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from . import __version__, browser_auth
from . import ytmusic_client as ytm
from .cache import Cache
from .spotify_client import get_spotify_playlists, get_spotify_tracks
from .transfer import transfer_spotify_playlist

console = Console()
cache = Cache()

_PRIVACY_CHOICES = ("PRIVATE", "PUBLIC", "UNLISTED")

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def _banner() -> str:
    """Render the ASCII art logo used on the welcome screen."""
    return Figlet(font="standard").renderText("spotify2yt").rstrip()


def _print_playlists(playlists: list[dict[str, str]], *, identifier: str) -> None:
    """Render a playlist list as a table with an index column."""
    if not playlists:
        console.print("[yellow]No playlists found.[/yellow]")
        return

    table = Table(box=box.ROUNDED, header_style="bold cyan")
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column(identifier.upper(), style="dim", overflow="fold")

    for index, playlist in enumerate(playlists, start=1):
        table.add_row(str(index), playlist["name"], playlist[identifier])

    console.print(table)


def _pick_playlist(playlists: list[dict[str, str]], *, identifier: str) -> str | None:
    """Show playlists and return the identifier of the playlist the user picks."""
    _print_playlists(playlists, identifier=identifier)
    if not playlists:
        return None

    if len(playlists) == 1:
        return playlists[0][identifier]

    choice = Prompt.ask(
        "[bold cyan]Select a playlist[/bold cyan]",
        choices=[str(i) for i in range(1, len(playlists) + 1)],
        show_choices=False,
    )
    return playlists[int(choice) - 1][identifier]


def _check_privacy(privacy: str) -> str:
    """Normalize and validate the playlist privacy setting."""
    privacy = privacy.upper()
    if privacy not in _PRIVACY_CHOICES:
        console.print(
            f"[red]Privacy must be one of: {', '.join(_PRIVACY_CHOICES)}.[/red]"
        )
        raise typer.Exit(code=1)
    return privacy


app = typer.Typer(
    name="spotify2yt",
    help="[bold]Migrate playlists between Spotify and YouTube Music.[/bold]",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)

spotify_app = typer.Typer(
    name="spotify",
    help="Work with your Spotify playlists.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

ytmusic_app = typer.Typer(
    name="ytmusic",
    help="Work with your YouTube Music playlists.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

transfer_app = typer.Typer(
    name="transfer",
    help="Transfer playlists from Spotify to YouTube Music.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

cache_app = typer.Typer(
    name="cache",
    help="Manage the local cache.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(spotify_app)
app.add_typer(ytmusic_app)
app.add_typer(transfer_app)
app.add_typer(cache_app)


# GLOBAL COMMANDS


@app.command()
def start() -> None:
    """Show the welcome screen with the available commands."""
    console.print(_banner(), style="bold cyan")
    console.print("[bold]Welcome to [cyan]spotify2yt[/cyan]![/bold]\n")
    console.print("Run [bold]spotify2yt --help[/bold] to see all commands.\n")

    table = Table(box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Command", style="bold")
    table.add_column("Description")
    table.add_row("spotify", "Work with your Spotify playlists")
    table.add_row("ytmusic", "Work with your YouTube Music playlists")
    table.add_row("transfer", "Transfer playlists from Spotify to YouTube Music")
    table.add_row("cache", "Manage the local cache")
    table.add_row("version", "Show the version of spotify2yt")
    console.print(table)


@app.command()
def version() -> None:
    """Show the version of spotify2yt."""
    console.print(f"[bold cyan]spotify2yt[/bold cyan] [dim]v{__version__}[/dim]")


# SPOTIFY COMMANDS


@spotify_app.command("playlists")
def spotify_playlists() -> None:
    """List your Spotify playlists."""
    with console.status("[bold cyan]Fetching Spotify playlists...[/bold cyan]"):
        playlists = get_spotify_playlists()
    _print_playlists(playlists, identifier="link")


@spotify_app.command("import")
def spotify_import(
    url: str | None = typer.Argument(None, help="Spotify playlist URL."),
) -> None:
    """Fetch the tracks of a Spotify playlist into the local cache.

    If no URL is given, you can pick one of your playlists interactively.
    """
    if url is None:
        with console.status("[bold cyan]Fetching Spotify playlists...[/bold cyan]"):
            playlists = get_spotify_playlists()
        url = _pick_playlist(playlists, identifier="link")
        if url is None:
            raise typer.Exit(code=1)

    with console.status("[bold cyan]Fetching Spotify playlist...[/bold cyan]"):
        tracks = get_spotify_tracks(url)

    cache.spotify_tracks = tracks
    cache.save()
    console.print(
        f"[green]Imported [bold]{len(tracks)}[/bold] tracks from Spotify.[/green]"
    )


# YOUTUBE MUSIC COMMANDS


@ytmusic_app.command("playlists")
def ytmusic_playlists() -> None:
    """List your YouTube Music playlists."""
    with console.status("[bold cyan]Fetching YouTube Music playlists...[/bold cyan]"):
        playlists = ytm.get_ytmusic_playlists()
    _print_playlists(playlists, identifier="id")


@ytmusic_app.command("import")
def ytmusic_import(
    playlist_id: str | None = typer.Argument(None, help="YouTube Music playlist ID."),
) -> None:
    """Fetch the tracks of a YouTube Music playlist into the local cache.

    If no ID is given, you can pick one of your playlists interactively.
    """
    if playlist_id is None:
        with console.status(
            "[bold cyan]Fetching YouTube Music playlists...[/bold cyan]"
        ):
            playlists = ytm.get_ytmusic_playlists()
        playlist_id = _pick_playlist(playlists, identifier="id")
        if playlist_id is None:
            raise typer.Exit(code=1)

    with console.status("[bold cyan]Fetching YouTube Music playlist...[/bold cyan]"):
        tracks = ytm.get_ytmusic_playlist_tracks(playlist_id)

    cache.ytmusic_tracks = tracks
    cache.save()
    console.print(
        f"[green]Imported [bold]{len(tracks)}[/bold] tracks from YouTube Music.[/green]"
    )


@ytmusic_app.command("search")
def ytmusic_search() -> None:
    """Search the imported Spotify tracks on YouTube Music and store their IDs."""
    if not cache.spotify_tracks:
        console.print(
            "[red]No Spotify tracks in cache. "
            "Run [bold]spotify import[/bold] first.[/red]"
        )
        raise typer.Exit(code=1)

    console.print("[cyan]Searching for tracks on YouTube Music...[/cyan]")
    cache.ytmusic_songsid = [
        song_id
        for song_id in ytm.search_songs_ytmusic(cache.spotify_tracks)
        if song_id is not None
    ]
    cache.save()
    console.print(
        f"[green]Found [bold]{len(cache.ytmusic_songsid)}[/bold] "
        f"of {len(cache.spotify_tracks)} tracks.[/green]"
    )


@ytmusic_app.command("auto-auth")
def ytmusic_auto_auth(
    browser: str = typer.Option(
        None,
        "--browser",
        "-b",
        help="Browser to read cookies from (firefox, chrome, chromium, brave, "
        "edge, opera). Omit to try every supported browser.",
    ),
) -> None:
    """Authenticate by reading YouTube Music cookies from your browser.

    Creates a validated browser.json without any manual header copying.
    Close the browser first so its cookie database is accessible.
    """
    with console.status("[bold cyan]Extracting cookies from browser...[/bold cyan]"):
        try:
            auth_file = browser_auth.auto_authenticate(browser)
        except Exception as exc:  # noqa: BLE001 - report any extraction failure cleanly
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from None

    console.print(
        f"[green]Authenticated successfully! "
        f"Auth file saved to [bold]{auth_file}[/bold].[/green]"
    )


@ytmusic_app.command("create")
def ytmusic_create(
    name: str = typer.Argument(..., help="Name of the new playlist."),
    privacy: str = typer.Option(
        "PRIVATE",
        "--privacy",
        "-p",
        help="Playlist privacy: PRIVATE, PUBLIC or UNLISTED.",
    ),
) -> None:
    """Create a playlist on YouTube Music from the cached song IDs."""
    if not cache.ytmusic_songsid:
        console.print(
            "[red]No song IDs in cache. Run [bold]ytmusic search[/bold] first.[/red]"
        )
        raise typer.Exit(code=1)

    privacy = _check_privacy(privacy)

    with console.status("[bold cyan]Creating playlist...[/bold cyan]"):
        result = ytm.create_ytmusic_playlist(name, privacy, cache.ytmusic_songsid)

    console.print(f"[green]{result}[/green]")


# TRANSFER COMMANDS


@transfer_app.command("all")
def transfer_all(
    privacy: str = typer.Option(
        "PRIVATE",
        "--privacy",
        "-p",
        help="Playlist privacy: PRIVATE, PUBLIC or UNLISTED.",
    ),
) -> None:
    """Transfer all your Spotify playlists to YouTube Music."""
    privacy = _check_privacy(privacy)

    with console.status("[bold cyan]Fetching Spotify playlists...[/bold cyan]"):
        playlists = get_spotify_playlists()

    if not playlists:
        console.print("[yellow]No Spotify playlists found.[/yellow]")
        raise typer.Exit(code=1)

    for playlist in playlists:
        console.rule(f"[bold cyan]{playlist['name']}[/bold cyan]")
        result = transfer_spotify_playlist(
            cache,
            playlist["link"],
            name=playlist["name"],
            privacy=privacy,
        )
        console.print(f"[green]{result}[/green]")

    console.print("[bold green]Transfer complete![/bold green]")


@transfer_app.command("quick")
def transfer_quick(
    url: str = typer.Argument(..., help="Spotify playlist URL."),
    privacy: str = typer.Option(
        "PRIVATE",
        "--privacy",
        "-p",
        help="Playlist privacy: PRIVATE, PUBLIC or UNLISTED.",
    ),
) -> None:
    """Transfer a single Spotify playlist to YouTube Music."""
    privacy = _check_privacy(privacy)

    console.rule("[bold cyan]Transferring playlist[/bold cyan]")
    result = transfer_spotify_playlist(cache, url, privacy=privacy)
    console.print(f"[green]{result}[/green]")


# CACHE COMMANDS


@cache_app.command("show")
def cache_show() -> None:
    """Show what is currently stored in the cache."""
    table = Table(box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Key", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("Spotify tracks", str(len(cache.spotify_tracks)))
    table.add_row("YouTube Music tracks", str(len(cache.ytmusic_tracks)))
    table.add_row("YouTube Music song IDs", str(len(cache.ytmusic_songsid)))
    console.print(table)


@cache_app.command("clear")
def cache_clear() -> None:
    """Delete all cached data."""
    cache.clear()
    console.print("[green]Cache cleared.[/green]")


def main() -> None:
    """Entry point used by the console script and ``python -m spotify2yt``.

    When the project is frozen to a standalone executable with PyInstaller the
    data files are unpacked into ``sys._MEIPASS``, so we switch to that
    directory before running the app to keep relative paths working.
    """
    if getattr(sys, "frozen", False):
        os.chdir(sys._MEIPASS)  # type: ignore[attr-defined]  # only set by PyInstaller

    try:
        app()
    except typer.Exit:
        raise
    except Exception as exc:  # noqa: BLE001 - surface a clean error instead of a traceback
        console.print(f"[red]Error: {exc}[/red]")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
