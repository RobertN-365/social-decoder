"""Tests for popup module."""
import pytest
from unittest.mock import patch, MagicMock


SAMPLE_RESULT = {
    "neutrality_score": 7,
    "likely_intent": "Scheduling a routine check-in.",
    "emotional_tone": "Neutral/Professional",
    "what_they_probably_mean": "They want to sync on project status.",
    "reassurance": "This is a normal workplace interaction.",
    "suggested_responses": ["Sure! When works best?", "Happy to chat."],
}

ERROR_RESULT = {"error": "Invalid API key. Please check your key in Settings."}


def test_clamp_position_within_screen():
    """Popup position should be clamped to screen bounds."""
    from popup import clamp_position
    x, y = clamp_position(100, 100, 400, 300, 1920, 1080)
    assert x == 100 + 12  # cursor_x + 12
    assert y == 100 + 12  # cursor_y + 12


def test_clamp_position_near_right_edge():
    """Popup should shift left when near right screen edge."""
    from popup import clamp_position
    x, y = clamp_position(1800, 100, 400, 300, 1920, 1080)
    assert x <= 1920 - 400  # Must fit on screen


def test_clamp_position_near_bottom_edge():
    """Popup should shift up when near bottom screen edge."""
    from popup import clamp_position
    x, y = clamp_position(100, 900, 400, 300, 1920, 1080)
    assert y <= 1080 - 300


def test_popup_creation_does_not_crash():
    """Popup should create without errors (smoke test)."""
    from popup import DecodePopup
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        popup = DecodePopup(root)
        popup.show_result(SAMPLE_RESULT, x=100, y=100)
        assert popup.window.winfo_exists()
        popup._immediate_close()
    finally:
        root.destroy()


def test_popup_error_display():
    """Popup should handle error results without crashing."""
    from popup import DecodePopup
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        popup = DecodePopup(root)
        popup.show_error("Invalid API key. Please check your key in Settings.")
        assert popup.window.winfo_exists()
        popup._immediate_close()
    finally:
        root.destroy()
