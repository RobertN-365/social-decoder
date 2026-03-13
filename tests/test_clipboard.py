"""Tests for clipboard module."""
import pytest
from unittest.mock import patch, MagicMock, call


@patch("clipboard.time")
@patch("clipboard.pyperclip")
@patch("clipboard.keyboard")
def test_get_selected_text_reads_clipboard(mock_keyboard, mock_pyperclip, mock_time):
    """Should simulate Ctrl+C and return clipboard contents."""
    from clipboard import get_selected_text

    # paste() called twice: first to save original, then to read after Ctrl+C
    mock_pyperclip.paste.side_effect = ["old content", "We need to talk"]

    result = get_selected_text()
    assert result == "We need to talk"
    mock_keyboard.send.assert_called_once_with("ctrl+c")
    # Should release modifiers before Ctrl+C, then wait after
    assert mock_time.sleep.call_count == 2


@patch("clipboard.time")
@patch("clipboard.pyperclip")
@patch("clipboard.keyboard")
def test_get_selected_text_restores_clipboard(mock_keyboard, mock_pyperclip, mock_time):
    """Should restore original clipboard after reading selection."""
    from clipboard import get_selected_text

    mock_pyperclip.paste.side_effect = ["original clipboard", "selected text"]

    get_selected_text()
    # copy() called twice: once to clear clipboard, once to restore original
    calls = mock_pyperclip.copy.call_args_list
    assert call("") in calls
    assert call("original clipboard") in calls


@patch("clipboard.time")
@patch("clipboard.pyperclip")
@patch("clipboard.keyboard")
def test_get_selected_text_empty_returns_none(mock_keyboard, mock_pyperclip, mock_time):
    """Should return None if clipboard is empty after Ctrl+C."""
    from clipboard import get_selected_text

    # After clearing and Ctrl+C, clipboard is still empty = nothing selected
    mock_pyperclip.paste.side_effect = ["old content", ""]

    result = get_selected_text()
    assert result is None
