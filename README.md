# spotify2yt — Spotify to YouTube Music CLI

A modern Python CLI tool that transfers tracks from a Spotify playlist to a YouTube Music playlist using `spotipy` and `ytmusicapi`.

## Features

- Fetch tracks from a Spotify playlist
- Fetch tracks from a YouTube Music playlist
- Search Spotify tracks on YouTube Music
- Create playlists on YouTube Music
- Transfer one or all Spotify playlists to YouTube Music

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python 3.11+
- Spotify Developer App (Client ID and Secret)
- YouTube Music authentication headers

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd spotify-to-ytmusic

# Create the virtual environment and install dependencies
# (includes the dev tools: ruff, mypy, pytest)
uv sync
```

The `uv sync` command reads `pyproject.toml` and installs the project plus all
dependencies (including the `dev` group with ruff, mypy and pytest) into a
local `.venv`. The lockfile `uv.lock` guarantees a reproducible environment.

## Configuration

### 1. Spotify Credentials

1. Go to https://developer.spotify.com/dashboard and create an app.
2. Fill the fields to create the app.
3. In "Redirect URIs" put `http://127.0.0.1:8888/callback`.

Create a `.env` file in the project root:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

### 2. YouTube Music Authentication

Run:

```
uv run ytmusicapi oauth
```

This generates a `headers_auth.json` file containing your session headers.

> Note: if your auth file has a different name, point to it with the
> `HEADERS_AUTH_PATH` environment variable in `.env`.

### 2.1 YouTube Music Authentication Browser

This is the easiest method and is recommended for Firefox.

1. Open your browser and go to https://music.youtube.com/
2. Open the Developer Tools and go to the Network tab.
3. Filter requests by searching for `https://music.youtube.com/youtubei/v1/`.
4. Find a POST request and copy its request headers.

Then, in your terminal, run:

```
uv run ytmusicapi browser
```

Paste the request; it generates a `browser.json` file with your session
headers.

> Remember: this method needs to be repeated fairly often. Test the file with
> `uv run spotify2yt ytmusic check`.

### 2.2 Automatic Authentication (recommended)

Instead of copying headers manually, let the tool read the cookies straight
from your browser:

```
uv run spotify2yt ytmusic auto-auth
# or target a specific browser:
uv run spotify2yt ytmusic auto-auth --browser firefox
```

Sign in to https://music.youtube.com in the browser first, and close the
browser so its cookie database is accessible. The command validates the
session before writing `browser.json`.

## Usage

```bash
# Show the welcome screen
uv run spotify2yt start

# Show the CLI help
uv run spotify2yt --help
```

### Available Commands

**Spotify:**
- `uv run spotify2yt spotify playlists` — List your Spotify playlists
- `uv run spotify2yt spotify import <URL>` — Import tracks from a Spotify playlist

**YouTube Music:**
- `uv run spotify2yt ytmusic playlists` — List your YouTube Music playlists
- `uv run spotify2yt ytmusic import <ID>` — Import tracks from a YouTube Music playlist
- `uv run spotify2yt ytmusic search` — Search for imported Spotify tracks on YouTube Music
- `uv run spotify2yt ytmusic create <NAME>` — Create a new YouTube Music playlist
- `uv run spotify2yt ytmusic check` — Test the YouTube Music connection
- `uv run spotify2yt ytmusic auto-auth` — Authenticate via browser cookies

**Transfer:**
- `uv run spotify2yt transfer all` — Transfer all your Spotify playlists to YouTube Music
- `uv run spotify2yt transfer quick <URL>` — Quickly transfer a single Spotify playlist

**Utility:**
- `uv run spotify2yt clear-cache` — Clear all cached data

### Shortcut Scripts

Convenience runners are included for each platform (all delegate to `uv run`):

| Script      | Platform        |
| ----------- | --------------- |
| `run.sh`    | Unix / Linux / Mac |
| `run.bat`   | Windows Batch   |
| `run.ps1`   | PowerShell      |

For example: `./run.sh transfer quick <URL>`.

## Development

The project follows modern Python practices: `src` layout, strict type
checking, linting and formatting with Ruff, and pytest for testing.

```bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy src

# Run tests
uv run pytest
```

## Project Structure

```
spotify-to-ytmusic/
├── src/spotify2yt/          (Application code)
│   ├── __init__.py          (Package metadata/version)
│   ├── __main__.py          (python -m spotify2yt entry point)
│   ├── cli.py               (Typer CLI)
│   ├── cache.py             (File-backed session cache)
│   ├── config.py            (Environment settings)
│   ├── logging.py           (Logging setup)
│   ├── models.py            (Track/Playlist dataclasses)
│   ├── spotify_client.py    (Spotify API client)
│   ├── transfer.py          (Transfer orchestration)
│   └── ytmusic_client.py    (YouTube Music client)
├── tests/                   (pytest suite)
├── .env.example             (Configuration template)
├── .python-version          (Pinned Python version for uv)
├── pyproject.toml           (Dependencies + tooling config)
├── uv.lock                  (Locked dependency tree)
└── README.md
```

## License

MIT License.