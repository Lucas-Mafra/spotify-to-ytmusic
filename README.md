# spotify2yt - Spotify to YouTube Music CLI 

A simple **Python CLI tool** that copies tracks from a
**Spotify playlist** to a **YouTube Music playlist**, using the `spotipy` and `ytmusicapi`.

## Features

-   Fetch tracks (title + artist) from Spotify and YouTube Music playlist
-   Create a playlist on YouTube Music based on the songs added to the Spotify playlist.
-   Simple and easy to run locally
-   Works entirely via terminal

## Requirements

-   Python 3.10+
-   A Spotify Developer App (Client ID & Secret)
-   YouTube Music authentication headers
-   Dependencies:
    -   `typer`
    -   `spotipy`
    -   `ytmusicapi`
    -   `rich`

## Configuration

### 1. Spotify Credentials

Create a `.env` file:

    SPOTIFY_CLIENT_ID=your_client_id
    SPOTIFY_CLIENT_SECRET=your_client_secret
    SPOTIFY_REDIRECT_URI=http://localhost:8888/callback

### 2. YouTube Music Auth

Generate your headers:

    ytmusicapi oauth

This will create `headers_auth.json`.

## Usage

Run the CLI:

    python main.py

## Project Structure

    spotify-to-ytmusic/
    │── spotify2yt/
    │   │── __init__.py
    │   │── cli.py
    │   │── compare.py
    │   │── conection_test.py
    │   │── spotify_client.py
    │   │── ytmusic_client.py
    │── pyproject.toml
    │── README.md
    │── requirements.txt

## Technologies

-   Python
-   Typer
-   Spotipy
-   ytmusicapi
-   Rich


## Contributing

Pull requests are welcome.

