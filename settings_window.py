"""Settings dialog window."""
import tkinter as tk
import threading
import sys
import os
import webbrowser
from theme import get_theme

GEMINI_KEY_URL = "https://aistudio.google.com/apikey"
STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "SocialDecoder"


class SettingsWindow:
    """Settings dialog for configuring the app."""

    def __init__(self, root: tk.Tk, config, on_save=None, theme_name: str = "dark"):
        self.root = root
        self.config = config
        self.on_save = on_save
        self.theme = get_theme(theme_name)
        self._build()

    def _build(self):
        t = self.theme
        self.window = tk.Toplevel(self.root)
        self.window.title("Social Decoder - Settings")
        self.window.configure(bg=t["bg"])
        self.window.resizable(False, True)
        self.window.geometry("440x480")
        self.window.grab_set()

        # Center on screen
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - 440) // 2
        y = (sh - 480) // 2
        self.window.geometry(f"+{x}+{y}")

        tk.Label(
            self.window, text="Settings", font=("Segoe UI", 14, "bold"),
            bg=t["bg"], fg=t["text"],
        ).pack(pady=(16, 12))

        form = tk.Frame(self.window, bg=t["bg"])
        form.pack(fill="x", padx=28)

        # API Key
        tk.Label(
            form, text="API Key", font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["text"], anchor="w",
        ).pack(fill="x", pady=(0, 2))

        key_row = tk.Frame(form, bg=t["bg"])
        key_row.pack(fill="x", pady=(0, 8))

        self.key_entry = tk.Entry(
            key_row, show="*", font=("Segoe UI", 10),
            bg=t["surface"], fg=t["text"], insertbackground=t["text"],
            relief="flat", bd=0,
            highlightbackground=t["border"], highlightthickness=1,
        )
        self.key_entry.pack(side="left", fill="x", expand=True, ipady=6)

        # Pre-fill if key exists
        existing_key = self.config.get_api_key()
        if existing_key:
            self.key_entry.insert(0, existing_key)

        self.test_btn = tk.Label(
            key_row, text="Test", font=("Segoe UI", 9),
            bg=t["surface"], fg=t["accent"], cursor="hand2",
            padx=10, pady=5,
            highlightbackground=t["border"], highlightthickness=1,
        )
        self.test_btn.pack(side="right", padx=(4, 0))
        self.test_btn.bind("<Button-1>", lambda e: self._test_key())

        # Status area: selectable Text widget that auto-resizes for long errors
        self.test_status = tk.Text(
            form, font=("Segoe UI", 9), bg=t["bg"], fg=t["text_secondary"],
            relief="flat", bd=0, wrap="word", height=1,
            state="disabled", cursor="arrow",
            highlightthickness=0,
        )
        self.test_status.pack(fill="x", pady=(0, 4))

        # Link to Anthropic console
        api_link = tk.Label(
            form, text="Manage API keys at Google AI Studio",
            font=("Segoe UI", 9, "underline"), bg=t["bg"], fg=t["accent"],
            anchor="w", cursor="hand2",
        )
        api_link.pack(fill="x", pady=(0, 8))
        api_link.bind("<Button-1>", lambda e: webbrowser.open(GEMINI_KEY_URL))

        # Hotkey
        tk.Label(
            form, text="Hotkey", font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["text"], anchor="w",
        ).pack(fill="x", pady=(0, 2))

        self.hotkey_entry = tk.Entry(
            form, font=("Segoe UI", 10),
            bg=t["surface"], fg=t["text"], insertbackground=t["text"],
            relief="flat", bd=0,
            highlightbackground=t["border"], highlightthickness=1,
        )
        self.hotkey_entry.insert(0, self.config.get("hotkey"))
        self.hotkey_entry.pack(fill="x", pady=(0, 12), ipady=6)

        # Decode mode
        tk.Label(
            form, text="Decode Mode", font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["text"], anchor="w",
        ).pack(fill="x", pady=(0, 2))

        self.mode_var = tk.StringVar(value=self.config.get("decode_mode"))
        for val, label in [
            ("nd", "I'm neurodivergent — decode NT messages for me"),
            ("nt", "I'm neurotypical — help me understand ND communication"),
        ]:
            tk.Radiobutton(
                form, text=label, variable=self.mode_var, value=val,
                font=("Segoe UI", 9), bg=t["bg"], fg=t["text"],
                selectcolor=t["surface"], activebackground=t["bg"],
                activeforeground=t["text"], anchor="w", wraplength=360,
            ).pack(fill="x", pady=(0, 2))

        # Spacer before theme
        tk.Frame(form, bg=t["bg"], height=8).pack(fill="x")

        # Theme
        tk.Label(
            form, text="Theme", font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["text"], anchor="w",
        ).pack(fill="x", pady=(0, 2))

        self.theme_var = tk.StringVar(value=self.config.get("theme"))
        theme_row = tk.Frame(form, bg=t["bg"])
        theme_row.pack(fill="x", pady=(0, 12))
        for val, label in [("dark", "Dark"), ("light", "Light")]:
            tk.Radiobutton(
                theme_row, text=label, variable=self.theme_var, value=val,
                font=("Segoe UI", 10), bg=t["bg"], fg=t["text"],
                selectcolor=t["surface"], activebackground=t["bg"],
                activeforeground=t["text"],
            ).pack(side="left", padx=(0, 16))

        # Start on boot
        self.boot_var = tk.BooleanVar(value=self.config.get("start_on_boot"))
        tk.Checkbutton(
            form, text="Start on boot", variable=self.boot_var,
            font=("Segoe UI", 10), bg=t["bg"], fg=t["text"],
            selectcolor=t["surface"], activebackground=t["bg"],
            activeforeground=t["text"],
        ).pack(fill="x", pady=(0, 16), anchor="w")

        # Save button
        save_btn = tk.Label(
            self.window, text="Save", font=("Segoe UI", 11, "bold"),
            bg=t["accent"], fg="#ffffff", cursor="hand2", padx=28, pady=10,
        )
        save_btn.pack(pady=(0, 16))
        save_btn.bind("<Button-1>", lambda e: self._save())

    def _set_status(self, msg: str, color: str):
        """Update the status Text widget and auto-resize window to fit."""
        w = self.test_status
        w.configure(state="normal")
        w.delete("1.0", "end")
        w.insert("1.0", msg)
        w.configure(state="disabled", fg=color)

        # Calculate how many lines the message needs at the current widget width
        self.window.update_idletasks()
        widget_width = w.winfo_width()
        if widget_width <= 1:
            widget_width = 376  # form width (440 - 2*32 padding)
        # Estimate chars per line from pixel width / avg char width (~7px for 9pt)
        chars_per_line = max(widget_width // 7, 20)
        import math
        num_lines = 0
        for line in msg.split("\n"):
            num_lines += max(1, math.ceil(len(line) / chars_per_line))
        w.configure(height=num_lines)

        # Allow cursor change to I-beam on error text so user can select/copy
        if color == self.theme["error"]:
            w.configure(cursor="ibeam")
        else:
            w.configure(cursor="arrow")

        # Resize window to fit content
        self.window.update_idletasks()
        self.window.geometry("")  # let tkinter auto-size

    def _test_key(self):
        key = self.key_entry.get().strip()
        if not key:
            self._set_status("Enter a key first", self.theme["error"])
            return
        self._set_status("Testing...", self.theme["text_secondary"])

        def do_test():
            from google import genai
            try:
                client = genai.Client(api_key=key)
                # Use the free list_models endpoint to validate the key
                list(client.models.list())
                msg = "Connected!"
                ok = True
            except Exception as e:
                ok = False
                err_str = str(e)
                if "API_KEY_INVALID" in err_str or "401" in err_str:
                    msg = "Invalid API key. Please check your key."
                else:
                    msg = f"Error: {e}"
            self.window.after(0, lambda: self._set_status(
                msg, self.theme["success"] if ok else self.theme["error"],
            ))

        threading.Thread(target=do_test, daemon=True).start()

    def _save(self):
        key = self.key_entry.get().strip()
        if key:
            self.config.set_api_key(key)
        self.config.set("hotkey", self.hotkey_entry.get().strip())
        self.config.set("decode_mode", self.mode_var.get())
        self.config.set("theme", self.theme_var.get())
        self.config.set("start_on_boot", self.boot_var.get())
        self.config.save()
        self._update_startup()
        if self.on_save:
            self.on_save()
        self.window.destroy()

    def _update_startup(self):
        """Add or remove from Windows startup registry."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE
            )
            if self.config.get("start_on_boot"):
                exe_path = sys.executable
                if getattr(sys, "frozen", False):
                    exe_path = sys.executable
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass  # Non-critical: startup registration can fail silently
