"""
Unit tests for Storage and Memory Engine
"""
import pytest
import tempfile
from pathlib import Path
from engine.storage import (
    atomic_write_json, load_json, save_report, load_latest_report,
    record_user_feedback, load_preferences
)


def test_atomic_write_and_load(tmp_path):
    test_file = tmp_path / "test.json"
    data = {"project": "AI Morning Agent", "status": "active"}
    
    assert atomic_write_json(test_file, data) is True
    loaded = load_json(test_file)
    assert loaded == data


def test_record_user_feedback_updates_preferences():
    prefs = record_user_feedback(
        story_headline="New Fab in Dholera",
        story_category="Semiconductors & Hardware",
        feedback_type="useful"
    )
    assert prefs is not None
    assert "Semiconductors & Hardware" in prefs["topic_weights"]
    # Should have increased weight above baseline
    assert prefs["topic_weights"]["Semiconductors & Hardware"] >= 1.15
