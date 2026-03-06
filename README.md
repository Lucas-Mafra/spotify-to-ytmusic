# spotify2yt — Spotify to YouTube Music CLI

A simple Python CLI tool that transfers tracks from a Spotify playlist to a YouTube Music playlist using `spotipy` and `ytmusicapi`.

## Features

- Fetch tracks (title and artist) from a Spotify playlist  
- Fetch tracks from a YouTube Music playlist  
- Search Spotify tracks on YouTube Music  
- Create playlists on YouTube Music  

## Architecture

This is an **executable-only project** - it's designed to be run directly as a command-line tool rather than installed as a Python package. The application is self-contained and can be:

- Run directly with `python main.py`

All code is in the `spotify2yt/` directory, and `main.py` serves as the entry point.


## Requirements

- Python 3.10+
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
3. The field "Redirect URIs" put http://127.0.0.1:8888/callback.

Create a `.env` file in the project root:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

### 2. YouTube Music Authentication

Run:

```
ytmusicapi oauth
```

This will generate a file:

```
headers_auth.json
```

This file contains your session headers used for authentication.

### 2.1  YouTube Music Authentication Browser

This is the method I believe is the easiest to follow. This method is recommended for Firefox.

1. Open your browser and go to → https://music.youtube.com/
2. Open the Developer Tools and go to the Network tab.
3. Filter the requests by searching for → https://music.youtube.com/youtubei/v1/
4. Find a POST request and copy its request headers.

After doing this, open your terminal and run:

```
ytmusicapi browser
```

Paste the request, and it will generate a file:

```
browser.json
```

This file contains your session headers. 

>Remember, this method will need to be repeated fairly often. I recommend running `python .\spotify2yt\conection_test.py` to test the `browser.json` file.



## Installation & Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd spotify-to-ytmusic

# Install Python dependencies
pip install -r requirements.txt
```

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
python main.py [command]
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
python -m spotify2yt [command]
```

### Welcome Screen

```bash
python main.py start
```

### Available Commands

**Spotify Commands:**
- `python main.py spotify playlists` - List your Spotify playlists
- `python main.py spotify import <URL>` - Import tracks from a Spotify playlist

**YouTube Music Commands:**
- `python main.py ytmusic playlists` - List your YouTube Music playlists  
- `python main.py ytmusic import <ID>` - Import tracks from a YouTube Music playlist
- `python main.py ytmusic search` - Search for imported Spotify tracks on YouTube Music
- `python main.py ytmusic create <NAME>` - Create a new YouTube Music playlist

**Transfer Commands:**
- `python main.py transfer all` - Transfer all your Spotify playlists to YouTube Music
- `python main.py transfer quick <URL>` - Quickly transfer a single Spotify playlist

**Utility Commands:**
- `python main.py clear-cache` - Clear all cached data


## Project Structure

```
spotify-to-ytmusic/
├── main.py                 (Executable entry point)
├── spotify2yt/             (Application code)
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── cache.py
│   ├── spotify_client.py
│   ├── ytmusic_client.py
│   └── conection_test.py
├── .env.example            (Configuration template)
├── .env                    (Configuration - not tracked)
├── pyproject.toml          (Dependencies)
├── requirements.txt        (Dependencies)
└── README.md
```

## Contributing

Pull requests are welcome.


## License

MIT License.
