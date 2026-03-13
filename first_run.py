"""First-run setup wizard dialog."""
import tkinter as tk
import threading
import webbrowser
from theme import get_theme

GEMINI_KEY_URL = "https://aistudio.google.com/apikey"


class FirstRunDialog:
    """First-run setup wizard for API key configuration."""

    def __init__(self, root: tk.Tk, config, theme_name: str = "dark"):
        self.root = root
        self.config = config
        self.theme = get_theme(theme_name)
        self.result = None  # "completed" or "cancelled"
        self._build()

    def _build(self):
        t = self.theme
        self.window = tk.Toplevel(self.root)
        self.window.title("Welcome to Social Decoder")
        self.window.configure(bg=t["bg"])
        self.window.resizable(False, False)
        self.window.geometry("480x520")
        self.window.grab_set()

        # Center on screen
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - 480) // 2
        y = (sh - 520) // 2
        self.window.geometry(f"+{x}+{y}")

        # Welcome
        tk.Label(
            self.window, text="Welcome to Social Decoder",
            font=("Segoe UI", 15, "bold"), bg=t["bg"], fg=t["text"],
        ).pack(pady=(24, 8))

        tk.Label(
            self.window,
            text="Highlight any text, press Ctrl+Shift+D, and get an\n"
                 "instant decode of the social subtext and emotional tone.",
            font=("Segoe UI", 10), bg=t["bg"], fg=t["text_secondary"],
            justify="center",
        ).pack(pady=(0, 16))

        # Mode selector
        mode_frame = tk.Frame(self.window, bg=t["bg"])
        mode_frame.pack(fill="x", padx=40)

        tk.Label(
            mode_frame, text="I am...", font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["text"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.mode_var = tk.StringVar(value="nd")
        for val, label in [
            ("nd", "Neurodivergent — help me decode neurotypical messages"),
            ("nt", "Neurotypical — help me understand neurodivergent communication"),
        ]:
            tk.Radiobutton(
                mode_frame, text=label, variable=self.mode_var, value=val,
                font=("Segoe UI", 9), bg=t["bg"], fg=t["text"],
                selectcolor=t["surface"], activebackground=t["bg"],
                activeforeground=t["text"], anchor="w", wraplength=380,
            ).pack(fill="x", pady=(0, 2))

        # API Key section
        key_frame = tk.Frame(self.window, bg=t["bg"])
        key_frame.pack(fill="x", padx=40)

        tk.Label(
            key_frame, text="Gemini API Key", font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["text"], anchor="w",
        ).pack(fill="x")

        self.key_entry = tk.Entry(
            key_frame, show="*", font=("Segoe UI", 10),
            bg=t["surface"], fg=t["text"], insertbackground=t["text"],
            relief="flat", bd=0,
            highlightbackground=t["border"], highlightthickness=1,
        )
        self.key_entry.pack(fill="x", pady=(4, 4), ipady=6)

        link = tk.Label(
            key_frame, text="Get your API key from Google AI Studio",
            font=("Segoe UI", 9, "underline"), bg=t["bg"], fg=t["accent"],
            cursor="hand2", anchor="w",
        )
        link.pack(fill="x")
        link.bind("<Button-1>", lambda e: webbrowser.open(GEMINI_KEY_URL))

        # Test button
        btn_frame = tk.Frame(self.window, bg=t["bg"])
        btn_frame.pack(fill="x", padx=40, pady=(12, 0))

        self.test_btn = tk.Label(
            btn_frame, text="Test Connection", font=("Segoe UI", 10),
            bg=t["surface"], fg=t["accent"], cursor="hand2",
            padx=12, pady=6,
            highlightbackground=t["border"], highlightthickness=1,
        )
        self.test_btn.pack(side="left")
        self.test_btn.bind("<Button-1>", lambda e: self._test_key())

        self.status_label = tk.Text(
            btn_frame, font=("Segoe UI", 9), bg=t["bg"], fg=t["text_secondary"],
            relief="flat", bd=0, wrap="word", height=1, width=30,
            state="disabled", cursor="arrow", highlightthickness=0,
        )
        self.status_label.pack(side="left", padx=(12, 0))

        # Hotkey info
        tk.Label(
            self.window,
            text="Hotkey: Ctrl+Shift+D (can be changed in Settings)",
            font=("Segoe UI", 9), bg=t["bg"], fg=t["text_secondary"],
        ).pack(pady=(20, 0))

        # Get Started button
        self.start_btn = tk.Label(
            self.window, text="Get Started", font=("Segoe UI", 12, "bold"),
            bg=t["accent"], fg="#ffffff", cursor="hand2", padx=28, pady=12,
        )
        self.start_btn.pack(pady=(20, 0))
        self.start_btn.bind("<Button-1>", lambda e: self._finish())

        self.window.protocol("WM_DELETE_WINDOW", self._cancel)

    def _set_status(self, msg, color):
        """Update the status text widget."""
        w = self.status_label
        w.configure(state="normal")
        w.delete("1.0", "end")
        w.insert("1.0", msg)
        w.configure(state="disabled", fg=color)
        # Auto-resize height
        import math
        chars_per_line = max(30, 1)
        num_lines = 0
        for line in msg.split("\n"):
            num_lines += max(1, math.ceil((len(line) or 1) / chars_per_line))
        w.configure(height=num_lines)
        if color == self.theme["error"]:
            w.configure(cursor="ibeam")
        else:
            w.configure(cursor="arrow")

    def _test_key(self):
        """Test the API key in a background thread using the free models endpoint."""
        key = self.key_entry.get().strip()
        if not key:
            self._set_status("Please enter a key", self.theme["error"])
            return

        self._set_status("Testing...", self.theme["text_secondary"])
        self.test_btn.configure(text="Testing...")

        def do_test():
            from google import genai
            try:
                client = genai.Client(api_key=key)
                list(client.models.list())
                self.window.after(0, lambda: self._show_test_result(True))
            except Exception as e:
                err_str = str(e)
                if "API_KEY_INVALID" in err_str or "401" in err_str:
                    msg = "Invalid API key. Please check your key."
                else:
                    msg = f"Error: {e}"
                self.window.after(0, lambda: self._show_test_result(False, msg))

        threading.Thread(target=do_test, daemon=True).start()

    def _show_test_result(self, success: bool, error_msg: str = ""):
        t = self.theme
        self.test_btn.configure(text="Test Connection")
        if success:
            self._set_status("Connected!", t["success"])
        else:
            display_msg = error_msg if error_msg else "Connection failed. Check your key."
            self._set_status(display_msg, t["error"])

    def _finish(self):
        """Save config and close."""
        key = self.key_entry.get().strip()
        if key:
            self.config.set_api_key(key)
        self.config.set("decode_mode", self.mode_var.get())
        self.config.save()
        self.result = "completed"
        self.window.destroy()

    def _cancel(self):
        self.result = "cancelled"
        self.window.destroy()

    def wait(self):
        """Block until the dialog is closed."""
        self.window.wait_window()
        return self.result
