# spotify2yt — Spotify to YouTube Music CLI

A simple Python CLI tool that transfers tracks from a Spotify playlist to a YouTube Music playlist using `spotipy` and `ytmusicapi`.

## Features

- Fetch tracks (title and artist) from a Spotify playlist  
- Fetch tracks from a YouTube Music playlist  
- Search Spotify tracks on YouTube Music  
- Create playlists on YouTube Music  


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



## Installation

In the project root (where `pyproject.toml` is located), run:

```
pip install -e .
```

This installs the CLI entry point `spotify2yt`.


## Usage


Start the welcome screen:

```
spotify2yt start
```

### Available Commands

| Command | Description |
|--------|-------------|
| `start` | Displays the welcome message and basic instructions |
| `getplaylists-spotify` | Lists all Spotify playlists for the user |
| `getplaylists-ytmusic` | Lists all Youtube Music playlists for the user |
| `import-spotify` | Imports tracks from a Spotify playlist |
| `import-ytmusic` | Imports tracks from a Youtube Music playlist |
| `searchsongs-ytmusic` | Searches for matching YouTube Music tracks |
| `create-ytmusic-playlist` | Creates a new playlist on YouTube Music |
| `clear-cache` | Clears local caches |

---

## Project Structure

```
spotify-to-ytmusic/
│── spotify2yt/
│   │── __init__.py
│   │── cli.py
│   │── conection_test.py
│   │── spotify_client.py
│   │── ytmusic_client.py
│── pyproject.toml
│── README.md
│── requirements.txt
```

## Contributing

Pull requests are welcome.


## License

MIT License.
