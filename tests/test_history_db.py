"""Tests for history database module."""
import tempfile
import os
import pytest


def test_save_and_retrieve_decode():
    """Should save a decode result and retrieve it."""
    from history_db import HistoryDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db = HistoryDB(os.path.join(tmpdir, "test.db"))
        db.save_decode(
            original_text="We need to talk",
            neutrality_score=7,
            emotional_tone="Neutral/Professional",
            likely_intent="Routine check-in",
            full_response='{"neutrality_score": 7}',
        )
        results = db.get_all()
        assert len(results) == 1
        assert results[0]["original_text"] == "We need to talk"
        assert results[0]["neutrality_score"] == 7


def test_search_by_text():
    """Should filter history by text content."""
    from history_db import HistoryDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db = HistoryDB(os.path.join(tmpdir, "test.db"))
        db.save_decode("We need to talk", 7, "Neutral", "Check-in", "{}")
        db.save_decode("Great job on the report", 9, "Positive", "Praise", "{}")

        results = db.search("talk")
        assert len(results) == 1
        assert results[0]["original_text"] == "We need to talk"


def test_get_by_id():
    """Should retrieve a single decode by ID."""
    from history_db import HistoryDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db = HistoryDB(os.path.join(tmpdir, "test.db"))
        db.save_decode("Hello", 8, "Friendly", "Greeting", '{"full": true}')

        results = db.get_all()
        row_id = results[0]["id"]
        single = db.get_by_id(row_id)
        assert single["full_response"] == '{"full": true}'


def test_clear_history():
    """Should delete all history entries."""
    from history_db import HistoryDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db = HistoryDB(os.path.join(tmpdir, "test.db"))
        db.save_decode("Msg 1", 5, "Neutral", "Intent", "{}")
        db.save_decode("Msg 2", 6, "Neutral", "Intent", "{}")
        assert len(db.get_all()) == 2

        db.clear_all()
        assert len(db.get_all()) == 0


def test_results_ordered_newest_first():
    """Results should come back with newest first."""
    from history_db import HistoryDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db = HistoryDB(os.path.join(tmpdir, "test.db"))
        db.save_decode("First", 5, "Neutral", "Intent", "{}")
        db.save_decode("Second", 6, "Neutral", "Intent", "{}")

        results = db.get_all()
        assert results[0]["original_text"] == "Second"
        assert results[1]["original_text"] == "First"
