"""Social Decoder — main entry point.

System tray app that decodes social subtext using Claude API.
"""
import json
import threading
import tkinter as tk
import sys
import os

from PIL import Image
import pystray
import keyboard

from config import Config
from decoder import decode_text, clarify_text
from clipboard import get_selected_text
from popup import DecodePopup
from history_db import HistoryDB
from first_run import FirstRunDialog
from settings_window import SettingsWindow
from history_window import HistoryWindow


class SocialDecoderApp:
    """Main application class wiring tray icon, hotkey, and GUI."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hidden root window

        self.config = Config()
        self.db = HistoryDB(self.config.db_path)
        self.popup = None
        self.tray_icon = None

        # Set app icon if available
        icon_path = self._get_icon_path()
        if icon_path and os.path.isfile(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

    def run(self):
        """Start the application."""
        # First-run setup
        if self.config.is_first_run:
            dialog = FirstRunDialog(self.root, self.config)
            result = dialog.wait()
            if result == "cancelled":
                self.root.destroy()
                return

        # Register global hotkey
        self._register_hotkey()

        # Start tray icon in a separate thread
        tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        tray_thread.start()

        # Run tkinter main loop
        self.root.mainloop()

    def _register_hotkey(self):
        """Register the global hotkey for decoding."""
        hotkey = self.config.get("hotkey")
        try:
            keyboard.add_hotkey(hotkey, self._on_hotkey)
        except Exception:
            self.root.after(2000, lambda: self._show_hotkey_error(hotkey))

    def _unregister_hotkey(self):
        """Remove all registered hotkeys."""
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

    def _on_hotkey(self):
        """Handle the decode hotkey press."""
        self.root.after(0, self._do_decode)

    def _do_decode(self):
        """Perform the full decode flow."""
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()

        selected = get_selected_text()
        if not selected:
            self._show_no_selection(x, y)
            return

        api_key = self.config.get_api_key()
        if not api_key:
            self.popup = DecodePopup(self.root, self.config.get("theme"))
            self.popup.set_on_settings(self._open_settings)
            self.popup.show_error("No API key configured. Please set one in Settings.", x, y)
            return

        self.popup = DecodePopup(self.root, self.config.get("theme"))
        self.popup.show_loading(x, y)

        def do_api_call():
            mode = self.config.get("decode_mode")
            result = decode_text(selected, api_key, mode=mode)
            self.root.after(0, lambda: self._show_decode_result(result, selected, x, y))

        threading.Thread(target=do_api_call, daemon=True).start()

    def _show_decode_result(self, result: dict, original_text: str, x: int, y: int):
        """Display the decode result or error."""
        if self.popup:
            self.popup.close()

        self.popup = DecodePopup(self.root, self.config.get("theme"))
        self.popup.set_on_settings(self._open_settings)
        self.popup.set_on_retry(self._do_decode)
        self.popup.set_on_clarify(self._do_clarify)

        if "error" in result:
            self.popup.show_error(result["error"], x, y)
        else:
            self.popup.show_result(result, x, y)
            self.db.save_decode(
                original_text=original_text,
                neutrality_score=result.get("neutrality_score", 5),
                emotional_tone=result.get("emotional_tone", "Unknown"),
                likely_intent=result.get("likely_intent", ""),
                full_response=json.dumps(result),
            )

    def _do_clarify(self, selected_text: str):
        """Perform a clarification request on the selected text."""
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()

        api_key = self.config.get_api_key()
        if not api_key:
            if self.popup:
                self.popup.close()
            self.popup = DecodePopup(self.root, self.config.get("theme"))
            self.popup.set_on_settings(self._open_settings)
            self.popup.show_error("No API key configured. Please set one in Settings.", x, y)
            return

        if self.popup:
            self.popup.close()
        self.popup = DecodePopup(self.root, self.config.get("theme"))
        self.popup.set_on_clarify(self._do_clarify)
        self.popup.show_loading(x, y, message="Clarifying...")

        def do_api_call():
            mode = self.config.get("decode_mode")
            result = clarify_text(selected_text, api_key, mode=mode)
            self.root.after(0, lambda: self._show_clarify_result(result, x, y))

        threading.Thread(target=do_api_call, daemon=True).start()

    def _show_clarify_result(self, result: str, x: int, y: int):
        """Display the clarification result."""
        if self.popup:
            self.popup.close()

        self.popup = DecodePopup(self.root, self.config.get("theme"))
        self.popup.set_on_clarify(self._do_clarify)

        if result.startswith("Error:"):
            self.popup.set_on_settings(self._open_settings)
            self.popup.show_error(result, x, y)
        else:
            self.popup.show_clarification(result, x, y)

    def _show_no_selection(self, x: int, y: int):
        """Show a brief tooltip for no selection."""
        if self.popup:
            self.popup.close()
        self.popup = DecodePopup(self.root, self.config.get("theme"))
        self.popup.show_error("No text selected. Highlight some text first.", x, y)

    def _show_hotkey_error(self, hotkey: str):
        """Notify user of hotkey conflict."""
        if self.popup:
            self.popup.close()
        self.popup = DecodePopup(self.root, self.config.get("theme"))
        self.popup.set_on_settings(self._open_settings)
        self.popup.show_error(
            f"Could not register hotkey '{hotkey}'. "
            "It may conflict with another app. Change it in Settings.",
            self.root.winfo_pointerx(), self.root.winfo_pointery(),
        )

    def _build_tray_menu(self):
        """Build the tray menu with the current hotkey displayed."""
        hotkey = self.config.get("hotkey")
        # Format hotkey for display: "ctrl+shift+d" -> "Ctrl+Shift+D"
        display_hotkey = "+".join(part.capitalize() for part in hotkey.split("+"))
        return pystray.Menu(
            pystray.MenuItem(f"Decode ({display_hotkey})", lambda: self.root.after(0, self._do_decode)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("History", lambda: self.root.after(0, self._open_history)),
            pystray.MenuItem("Settings", lambda: self.root.after(0, self._open_settings)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

    def _update_tray_menu(self):
        """Refresh the tray icon menu to reflect current settings."""
        if self.tray_icon:
            self.tray_icon.menu = self._build_tray_menu()
            self.tray_icon.update_menu()

    def _run_tray(self):
        """Run the system tray icon."""
        icon_image = self._load_tray_icon()
        menu = self._build_tray_menu()
        self.tray_icon = pystray.Icon("SocialDecoder", icon_image, "Social Decoder", menu)
        self.tray_icon.run()

    def _load_tray_icon(self) -> Image.Image:
        """Load the tray icon image."""
        icon_path = self._get_icon_path()
        if icon_path and os.path.isfile(icon_path):
            try:
                return Image.open(icon_path)
            except Exception:
                pass
        # Fallback: generate a simple colored square
        img = Image.new("RGB", (64, 64), "#60a5fa")
        return img

    def _get_icon_path(self) -> str:
        """Get path to the icon file."""
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        # Try .ico first, then .png
        for ext in (".ico", ".png"):
            path = os.path.join(base, f"icon{ext}")
            if os.path.isfile(path):
                return path
        return os.path.join(base, "icon.ico")

    def _open_settings(self):
        """Open the settings window."""
        def on_save():
            self._unregister_hotkey()
            self._register_hotkey()
            self._update_tray_menu()

        SettingsWindow(self.root, self.config, on_save=on_save, theme_name=self.config.get("theme"))

    def _open_history(self):
        """Open the history window."""
        HistoryWindow(self.root, self.db, theme_name=self.config.get("theme"))

    def _quit(self):
        """Clean shutdown."""
        self._unregister_hotkey()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)


def main():
    app = SocialDecoderApp()
    app.run()


if __name__ == "__main__":
    main()
