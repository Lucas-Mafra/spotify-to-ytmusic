# spotify2yt — Spotify to YouTube Music CLI

A simple Python CLI tool that transfers tracks from a Spotify playlist to a YouTube Music playlist using `spotipy` and `ytmusicapi`.

## Features

- Fetch tracks (title, artists, album and duration) from a Spotify playlist  
- Fetch tracks from a YouTube Music playlist  
- Smart track matching between Spotify and YouTube Music (see [Smart Track Matching](#smart-track-matching))  
- Create playlists on YouTube Music  

## Architecture

This is an **executable-only project** - it's designed to be run directly as a command-line tool rather than installed as a Python package. The application is self-contained and can be:

- Run directly with `uv run python main.py`

All code is in the `spotify2yt/` directory, and `main.py` serves as the entry point.

## Smart Track Matching

The most delicate part of any playlist migration is finding the *right* version of each song on the target service. Earlier versions of this tool simply took the **first search result**, which frequently imported covers, live recordings, remixes or completely unrelated videos. The matching is now metadata-driven and happens in three steps:

### 1. Structured metadata

Instead of a plain `"Artist Title"` string, Spotify now provides a structured track (`spotify2yt/matching.py::Track`) containing:

- **title** - e.g. `Lose Yourself (From "8 Mile" Soundtrack)`
- **artists** - all of them, in order (primary artist first)
- **album**
- **duration_ms**

### 2. Query normalization

Both sides of the comparison are normalized before scoring:

- Accents are removed and text is lowercased (`Café` → `cafe`)
- Upload noise inside brackets is dropped: `(Official Music Video)`, `[HD]`, `[Lyrics]`, `(Audio)`...
- Soundtrack suffixes are stripped: `(From "8 Mile" Soundtrack)`
- Edition tags are dropped: `- Remastered 2011`, `- Radio Edit`, `- Single Version`
- Featured artists are removed from titles: `feat.`, `ft.`, `featuring`
- Meaningful segments are preserved: `Sweet Dreams (Are Made of This)` stays intact

### 3. Candidate scoring

For every track, up to 5 candidates per category are fetched from YouTube Music and scored from 0 to 1:

| Signal   | Weight | How it works                                                                 |
| -------- | ------ | ---------------------------------------------------------------------------- |
| Title    | 60%    | Character-level similarity (difflib) combined with word overlap              |
| Artists  | 30%    | Primary artist counts 70%, second artist 20%, third 10% (features often omitted by YouTube Music) |
| Duration | 10%    | Linear penalty: identical length scores 1.0, 15+ seconds apart scores 0      |

### 4. Two-stage search

Candidates are searched in two stages, each with its own acceptance threshold:

1. **Songs** (score >= 0.75) - official catalog songs, preferred
2. **Videos** (score >= 0.85) - stricter fallback for tracks that only exist as uploads, since this bucket is full of covers and live takes

A track only enters the new playlist if it clears a threshold; otherwise it is skipped and reported with a warning instead of silently importing the wrong song.

### Tuning

All weights and thresholds live at the top of [`spotify2yt/matching.py`](spotify2yt/matching.py) (`SONG_MATCH_THRESHOLD`, `VIDEO_MATCH_THRESHOLD`, `TITLE_WEIGHT`, ...), so you can make matching stricter or more lenient without touching the logic.


## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Spotify Developer App (Client ID and Secret)
- YouTube Music authentication headers

### Dependencies

- typer  
- spotipy  
- ytmusicapi  
- python-dotenv  
- rich  


## Configuration

### 1. Spotify Credentials

1. Go to https://developer.spotify.com/dashboard and Create app.
2. Fill the fields to create the app.
3. In "Redirect URIs" put exactly `http://127.0.0.1:8888/callback`.

> Spotify no longer accepts `localhost` in redirect URIs - always use the loopback IP `127.0.0.1`, and make sure it matches **exactly** (protocol, host, port and path) between the dashboard and your `.env`.

Create a `.env` file in the project root:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### 2. YouTube Music Authentication

**Recommended: automatic browser authentication**

```
uv run python main.py ytmusic auto-auth
```

This reads your `music.youtube.com` cookies straight from your browser (Firefox, Chrome, Chromium, Brave, Edge or Opera), builds the auth headers and validates them - no manual copying. Requirements:

- You are signed in to https://music.youtube.com in that browser
- The browser is closed while running the command (its cookie database must be unlocked)

To target a specific browser:

```
uv run python main.py ytmusic auto-auth --browser firefox
```

The result is saved to `browser.json`.

> **Why not OAuth?** Since August 2025 YouTube Music rejects OAuth tokens from custom API clients on its internal endpoints ([ytmusicapi#813](https://github.com/sigma67/ytmusicapi/issues/813)), which surfaces as `HTTP 400: Request contains an invalid argument`. Browser authentication is the workaround recommended by the library maintainer.

### 2.1 Manual Browser Authentication

If the automatic extraction does not work for you, copy the headers manually:

1. Open your browser and go to → https://music.youtube.com/
2. Open the Developer Tools and go to the Network tab.
3. Filter the requests by searching for → https://music.youtube.com/youtubei/v1/
4. Find a POST request and copy its request headers.

After doing this, open your terminal and run:

```
uv run ytmusicapi browser
```

Paste the request, and it will generate a file:

```
browser.json
```

>Remember, this manual method will need to be repeated fairly often. I recommend running `uv run python .\spotify2yt\check_connection.py` to test the auth file.

**Auth file lookup:** the app automatically looks for `browser.json`, `headers_auth.json` or `oauth.json` in the project root. If your file has a different name or location, set `YTMUSIC_AUTH_FILE` in your `.env`.



## Installation & Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd spotify-to-ytmusic

# Install Python dependencies with uv
uv sync
```

The `uv sync` command reads `pyproject.toml` and installs all dependencies
into a local `.venv`. The lockfile `uv.lock` guarantees a reproducible
environment.

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your Spotify and YouTube Music credentials.



## Usage

### Running the Application

**Option 1: Direct Python (Cross-platform)**

```bash
uv run python main.py [command]
```

**Option 2: Windows Batch Script**

```bash
run.bat [command]
```

**Option 3: Windows PowerShell**

```bash
./run.ps1 [command]
```

**Option 4: Unix/Linux/Mac Shell**

```bash
./run.sh [command]
```

**Option 5: Python Module**

```bash
uv run python -m spotify2yt [command]
```

### Welcome Screen

```bash
uv run python main.py start
```

Running any command without arguments (e.g. `uv run python main.py`) shows the help.

### Available Commands

Run `uv run python main.py <group> --help` to see the commands of each group.

**Global:**
- `uv run python main.py start` - Show the welcome screen
- `uv run python main.py version` - Show the version of spotify2yt

**Spotify Commands:**
- `uv run python main.py spotify playlists` - List your Spotify playlists
- `uv run python main.py spotify import [URL]` - Import tracks from a Spotify playlist. Without a URL, you can pick one of your playlists interactively

**YouTube Music Commands:**
- `uv run python main.py ytmusic auto-auth [--browser BROWSER]` - Authenticate by reading cookies from your browser (recommended)
- `uv run python main.py ytmusic playlists` - List your YouTube Music playlists  
- `uv run python main.py ytmusic import [ID]` - Import tracks from a YouTube Music playlist. Without an ID, you can pick one of your playlists interactively
- `uv run python main.py ytmusic search` - Match the imported Spotify tracks on YouTube Music using fuzzy scoring
- `uv run python main.py ytmusic create NAME [--privacy PRIVATE|PUBLIC|UNLISTED]` - Create a new YouTube Music playlist

**Transfer Commands:**
- `uv run python main.py transfer all [--privacy PRIVATE]` - Transfer all your Spotify playlists to YouTube Music
- `uv run python main.py transfer quick URL [--privacy PRIVATE]` - Quickly transfer a single Spotify playlist

**Cache Commands:**
- `uv run python main.py cache show` - Show what is stored in the cache
- `uv run python main.py cache clear` - Clear all cached data


## Project Structure

```
spotify-to-ytmusic/
├── main.py                 (Executable entry point)
├── spotify2yt/             (Application code)
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              (CLI commands and presentation)
│   ├── transfer.py         (Transfer orchestration)
│   ├── matching.py         (Fuzzy track matching between services)
│   ├── browser_auth.py     (Automatic auth via browser cookies)
│   ├── cache.py
│   ├── spotify_client.py
│   ├── ytmusic_client.py
│   └── check_connection.py
├── .env.example            (Configuration template)
├── .env                    (Configuration - not tracked)
├── .python-version         (Pinned Python version for uv)
├── pyproject.toml          (Dependencies and tooling)
├── uv.lock                 (Locked dependency tree)
└── README.md
```

## Development

Run the checks before committing:

```bash
uv run ruff check spotify2yt/
uv run mypy spotify2yt/
```

## Contributing

Pull requests are welcome.


## License

MIT License.
