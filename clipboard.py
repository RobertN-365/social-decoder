"""Clipboard handling: save, simulate Ctrl+C, read, restore."""
import time
import pyperclip
import keyboard


def get_selected_text() -> str | None:
    """Simulate Ctrl+C to capture selected text, preserving clipboard.

    Returns the selected text, or None if nothing was selected.
    """
    # Save current clipboard
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    # Clear clipboard so we can detect if Ctrl+C actually captured anything
    try:
        pyperclip.copy("")
    except Exception:
        pass

    # Release any held modifier keys (Ctrl, Shift, Alt) from the hotkey combo
    # before simulating Ctrl+C, otherwise the OS sees Ctrl+Shift+C etc.
    for mod in ("ctrl", "shift", "alt"):
        try:
            keyboard.release(mod)
        except Exception:
            pass
    time.sleep(0.05)

    # Simulate Ctrl+C
    keyboard.send("ctrl+c")
    time.sleep(0.2)  # Brief pause for clipboard to update

    # Read new clipboard
    try:
        selected = pyperclip.paste()
    except Exception:
        selected = ""

    # Restore original clipboard
    try:
        pyperclip.copy(original)
    except Exception:
        pass

    # If clipboard is empty, nothing was selected/copied
    if not selected.strip():
        return None

    return selected.strip()
