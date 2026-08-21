"""Fuzzy matching used to pair Spotify tracks with YouTube Music results.

The old strategy took the first search result, which often picked covers,
live versions or unrelated videos. This module scores every candidate
against the original Spotify metadata (title, artists and duration) and
only accepts matches that are similar enough.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

# Score required to accept a candidate. Videos are held to a stricter
# standard because that bucket is full of covers, remixes and live takes.
SONG_MATCH_THRESHOLD = 0.75
VIDEO_MATCH_THRESHOLD = 0.85

# Relative importance of each signal in the final score.
TITLE_WEIGHT = 0.6
ARTIST_WEIGHT = 0.3
DURATION_WEIGHT = 0.1

# How much each artist matters: the primary artist is a much stronger
# signal than featured guests, which YouTube Music often omits.
ARTIST_WEIGHTS = (0.7, 0.2, 0.1)

# Duration difference (in seconds) at which the duration score reaches zero.
DURATION_PENALTY_SECONDS = 15.0

_FEAT_RE = re.compile(r"\b(?:feat\.?|featuring|ft\.?)\s+.*$", re.IGNORECASE)
_BRACKET_RE = re.compile(r"\([^()]*\)|\[[^\[\]]*\]")
# Bracketed segments containing these keywords are upload noise rather than
# part of the song title ("(Official Music Video)", "[Lyrics]", ...).
_NOISE_KEYWORDS = (
    "official",
    "video",
    "audio",
    "lyric",
    "hd",
    "hq",
    "4k",
    "remaster",
    "visualizer",
    "m/v",
)
# "(From "8 Mile" Soundtrack)" and friends: Spotify appends the source media
# to soundtrack titles, YouTube Music never does.
_FROM_RE = re.compile(
    r"\((?:from|do)\b[^()]*\)|\[(?:from|do)\b[^\[\]]*\]", re.IGNORECASE
)
# Dash-separated edition tags ("- Remastered 2011", "- Radio Edit", ...).
_EDITION_RE = re.compile(
    r"\s+-\s+(?:remaster(?:ed)?|radio edit|album version|single version"
    r"|extended(?: mix)?|deluxe|bonus track|bonus|edition)\b.*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Track:
    """A track with the metadata needed to match it across services."""

    title: str
    artists: tuple[str, ...] = ()
    album: str = ""
    duration_ms: int | None = None

    @property
    def query(self) -> str:
        """Build the search query sent to YouTube Music."""
        artist = self.artists[0] if self.artists else ""
        return f"{artist} {self.title}".strip()

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Track:
        """Rebuild a track from its cached dictionary representation."""
        artists = data.get("artists", [])
        duration = data.get("duration_ms")
        return cls(
            title=str(data.get("title", "")),
            artists=tuple(str(a) for a in artists) if isinstance(artists, list) else (),
            album=str(data.get("album", "")),
            duration_ms=int(duration) if isinstance(duration, (int, float)) else None,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation for the cache."""
        return {
            "title": self.title,
            "artists": list(self.artists),
            "album": self.album,
            "duration_ms": self.duration_ms,
        }


def _strip_noise(text: str) -> str:
    """Drop bracketed upload noise while keeping meaningful title segments."""

    def repl(match: re.Match[str]) -> str:
        content = match.group(0)
        noisy = any(kw in content.lower() for kw in _NOISE_KEYWORDS)
        return " " if noisy else content

    return _BRACKET_RE.sub(repl, text)


def normalize(text: str) -> str:
    """Lowercase, strip accents/punctuation and drop noise like "(Official Video)"."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = _FEAT_RE.sub(" ", text)
    text = _FROM_RE.sub(" ", text)
    text = _EDITION_RE.sub(" ", text)
    text = _strip_noise(text)
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    """Return a 0-1 similarity between two strings (0 when either is empty).

    Combines character-level similarity with word overlap so that titles
    with reordered or extra words still score well.
    """
    if not a or not b:
        return 0.0

    char_ratio = SequenceMatcher(None, a, b).ratio()
    words_a, words_b = set(a.split()), set(b.split())
    union = words_a | words_b
    word_ratio = len(words_a & words_b) / len(union) if union else 0.0
    return max(char_ratio, word_ratio)


def _duration_score(track_ms: int | None, candidate_seconds: float | None) -> float:
    """Score duration proximity; unknown durations count as neutral."""
    if track_ms is None or candidate_seconds is None:
        return 0.5
    diff = abs(track_ms / 1000 - candidate_seconds)
    return max(0.0, 1.0 - diff / DURATION_PENALTY_SECONDS)


def _artist_score(
    track_artists: tuple[str, ...], candidate_artists: list[str]
) -> float:
    """Compare Spotify artists against the candidate's weighted by importance."""
    if not track_artists or not candidate_artists:
        return 0.0

    normalized_candidates = [normalize(artist) for artist in candidate_artists]
    scores = [
        max(
            similarity(normalize(artist), candidate)
            for candidate in normalized_candidates
        )
        for artist in track_artists[: len(ARTIST_WEIGHTS)]
    ]
    weights = ARTIST_WEIGHTS[: len(scores)]
    total_weight = sum(weights)
    return (
        sum(score * weight for score, weight in zip(scores, weights, strict=True))
        / total_weight
    )


def score_match(
    track: Track,
    candidate_title: str,
    candidate_artists: list[str],
    candidate_duration_seconds: float | None = None,
) -> float:
    """Return a 0-1 score of how well a candidate matches a Spotify track."""
    title_score = similarity(normalize(track.title), normalize(candidate_title))
    artist_score = _artist_score(track.artists, candidate_artists)
    duration_score = _duration_score(track.duration_ms, candidate_duration_seconds)

    return (
        TITLE_WEIGHT * title_score
        + ARTIST_WEIGHT * artist_score
        + DURATION_WEIGHT * duration_score
    )
