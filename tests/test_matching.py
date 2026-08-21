"""Tests for the fuzzy matching module."""

from spotify2yt.matching import (
    SONG_MATCH_THRESHOLD,
    Track,
    normalize,
    score_match,
    similarity,
)


class TestNormalize:
    def test_lowercases_and_strips_punctuation(self):
        assert normalize("Hello, World!") == "hello world"

    def test_strips_accents(self):
        assert normalize("Beyoncé") == "beyonce"
        assert normalize("Sigur Rós") == "sigur ros"

    def test_removes_official_video_noise(self):
        assert normalize("Song Name (Official Music Video)") == "song name"

    def test_removes_bracketed_lyrics_tag(self):
        assert normalize("Song Name [Official Lyrics]") == "song name"

    def test_keeps_meaningful_parentheses(self):
        assert normalize("Song Name (Live)") == "song name live"

    def test_removes_feat_section(self):
        assert normalize("Song Name feat. Other Artist") == "song name"
        assert normalize("Song Name ft. Someone") == "song name"

    def test_removes_soundtrack_source(self):
        result = normalize('Song Name (From "8 Mile" Soundtrack)')
        assert result == "song name"

    def test_removes_edition_tags(self):
        assert normalize("Song Name - Remastered 2011") == "song name"
        assert normalize("Song Name - Radio Edit") == "song name"


class TestSimilarity:
    def test_identical_strings_score_one(self):
        assert similarity("same text", "same text") == 1.0

    def test_empty_string_scores_zero(self):
        assert similarity("", "something") == 0.0
        assert similarity("something", "") == 0.0

    def test_word_overlap_boosts_score(self):
        # Character ratio alone would be low; shared words lift the score.
        assert similarity("the quick brown fox", "brown fox quick the") > 0.9


class TestScoreMatch:
    def make_track(self):
        return Track(
            title="Bohemian Rhapsody",
            artists=("Queen",),
            album="A Night at the Opera",
            duration_ms=355_000,
        )

    def test_exact_match_scores_above_song_threshold(self):
        candidate = ("Bohemian Rhapsody", ["Queen"], 355.0)
        assert score_match(self.make_track(), *candidate) >= SONG_MATCH_THRESHOLD

    def test_unrelated_candidate_scores_low(self):
        candidate = ("Completely Different Song", ["Nobody"], 120.0)
        assert score_match(self.make_track(), *candidate) < 0.3

    def test_cover_by_other_artist_scores_below_exact(self):
        exact = score_match(
            self.make_track(), "Bohemian Rhapsody", ["Queen"], 355.0
        )
        cover = score_match(
            self.make_track(), "Bohemian Rhapsody", ["Panic! At The Disco"], 300.0
        )
        assert cover < exact

    def test_duration_is_only_a_small_signal(self):
        no_duration = score_match(self.make_track(), "Bohemian Rhapsody", ["Queen"])
        with_duration = score_match(
            self.make_track(), "Bohemian Rhapsody", ["Queen"], 355.0
        )
        assert with_duration > no_duration


class TestTrack:
    def test_query_prefers_primary_artist(self):
        track = Track(title="Song", artists=("Primary", "Guest"))
        assert track.query == "Primary Song"

    def test_query_without_artists_is_title_only(self):
        track = Track(title="Song")
        assert track.query == "Song"

    def test_dict_roundtrip(self):
        track = Track(
            title="Song",
            artists=("A", "B"),
            album="Album",
            duration_ms=200_000,
        )
        assert Track.from_dict(track.to_dict()) == track

    def test_from_dict_tolerates_missing_fields(self):
        track = Track.from_dict({})
        assert track.title == ""
        assert track.artists == ()
        assert track.album == ""
        assert track.duration_ms is None

    def test_from_dict_tolerates_bad_types(self):
        track = Track.from_dict({"title": 123, "artists": "not-a-list"})
        assert track.title == "123"
        assert track.artists == ()
