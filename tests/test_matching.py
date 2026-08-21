"""Tests for the fuzzy matching module."""

from spotify2yt.matching import (
    SONG_MATCH_THRESHOLD,
    normalize,
    score_match,
    similarity,
)
from spotify2yt.models import Track


def make_track() -> Track:
    return Track(
        artist="Queen",
        title="Bohemian Rhapsody",
        artists=("Queen",),
        album="A Night at the Opera",
        duration_ms=355_000,
    )


class TestNormalize:
    def test_lowercases_and_strips_punctuation(self) -> None:
        assert normalize("Hello, World!") == "hello world"

    def test_strips_accents(self) -> None:
        assert normalize("Beyoncé") == "beyonce"
        assert normalize("Sigur Rós") == "sigur ros"

    def test_removes_official_video_noise(self) -> None:
        assert normalize("Song Name (Official Music Video)") == "song name"

    def test_removes_bracketed_lyrics_tag(self) -> None:
        assert normalize("Song Name [Official Lyrics]") == "song name"

    def test_keeps_meaningful_parentheses(self) -> None:
        assert normalize("Song Name (Live)") == "song name live"

    def test_removes_feat_section(self) -> None:
        assert normalize("Song Name feat. Other Artist") == "song name"
        assert normalize("Song Name ft. Someone") == "song name"

    def test_removes_soundtrack_source(self) -> None:
        result = normalize('Song Name (From "8 Mile" Soundtrack)')
        assert result == "song name"

    def test_removes_edition_tags(self) -> None:
        assert normalize("Song Name - Remastered 2011") == "song name"
        assert normalize("Song Name - Radio Edit") == "song name"


class TestSimilarity:
    def test_identical_strings_score_one(self) -> None:
        assert similarity("same text", "same text") == 1.0

    def test_empty_string_scores_zero(self) -> None:
        assert similarity("", "something") == 0.0
        assert similarity("something", "") == 0.0

    def test_word_overlap_boosts_score(self) -> None:
        # Character ratio alone would be low; shared words lift the score.
        assert similarity("the quick brown fox", "brown fox quick the") > 0.9


class TestScoreMatch:
    def test_exact_match_scores_above_song_threshold(self) -> None:
        candidate = ("Bohemian Rhapsody", ["Queen"], 355.0)
        assert score_match(make_track(), *candidate) >= SONG_MATCH_THRESHOLD

    def test_unrelated_candidate_scores_low(self) -> None:
        candidate = ("Completely Different Song", ["Nobody"], 120.0)
        assert score_match(make_track(), *candidate) < 0.3

    def test_cover_by_other_artist_scores_below_exact(self) -> None:
        exact = score_match(make_track(), "Bohemian Rhapsody", ["Queen"], 355.0)
        cover = score_match(make_track(), "Bohemian Rhapsody", ["Panic! At The Disco"], 300.0)
        assert cover < exact

    def test_duration_is_only_a_small_signal(self) -> None:
        no_duration = score_match(make_track(), "Bohemian Rhapsody", ["Queen"])
        with_duration = score_match(make_track(), "Bohemian Rhapsody", ["Queen"], 355.0)
        assert with_duration > no_duration

    def test_featured_artists_are_weaker_signal_than_primary(self) -> None:
        featured = score_match(make_track(), "Bohemian Rhapsody", ["Freddie"], 355.0)
        primary = score_match(make_track(), "Bohemian Rhapsody", ["Queen"], 355.0)
        assert featured < primary
