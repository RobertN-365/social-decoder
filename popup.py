"""Decode result popup window."""
import tkinter as tk
import pyperclip
from theme import get_theme, score_color
from widgets import selectable_text

POPUP_WIDTH = 420
PADDING = 20


def _dim_color(hex_color: str, bg_color: str, factor: float = 0.4) -> str:
    """Blend hex_color toward bg_color by factor (0=original, 1=bg)."""
    def to_rgb(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r1, g1, b1 = to_rgb(hex_color)
    r2, g2, b2 = to_rgb(bg_color)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def clamp_position(
    cursor_x: int, cursor_y: int,
    popup_w: int, popup_h: int,
    screen_w: int, screen_h: int,
) -> tuple[int, int]:
    """Clamp popup position so it stays within screen bounds."""
    x = min(cursor_x + 12, screen_w - popup_w - 8)
    y = min(cursor_y + 12, screen_h - popup_h - 8)
    x = max(8, x)
    y = max(8, y)
    return x, y


class DecodePopup:
    """Frameless popup showing decode results near the cursor."""

    def __init__(self, root: tk.Tk, theme_name: str = "dark"):
        self.root = root
        self.theme = get_theme(theme_name)
        self.window = None
        self._on_settings_callback = None
        self._on_retry_callback = None
        self._on_clarify_callback = None
        self._after_ids = []  # Track after() IDs for cancellation

    def set_on_settings(self, callback):
        """Set callback for when user clicks 'Open Settings' in error view."""
        self._on_settings_callback = callback

    def set_on_retry(self, callback):
        """Set callback for when user clicks 'Retry' in error view."""
        self._on_retry_callback = callback

    def set_on_clarify(self, callback):
        """Set callback(selected_text) for right-click Clarify action."""
        self._on_clarify_callback = callback

    def show_result(self, result: dict, x: int = 100, y: int = 100):
        """Display a decode result popup at the given position."""
        self._create_window()
        t = self.theme
        clarify = self._on_clarify_callback

        # Header
        header = tk.Frame(self.window, bg=t["surface"])
        header.pack(fill="x", padx=PADDING, pady=(PADDING, 10))
        tk.Label(
            header, text="Social Decoder", font=("Segoe UI", 12, "bold"),
            bg=t["surface"], fg=t["text"],
        ).pack(side="left")
        self._close_button(header, t)

        # Neutrality Score
        score = result.get("neutrality_score", 5)
        sc = score_color(score, t)
        score_frame = tk.Frame(self.window, bg=t["bg"])
        score_frame.pack(fill="x", padx=PADDING, pady=(0, 10))
        tk.Label(
            score_frame, text=f"{score}/10", font=("Segoe UI", 22, "bold"),
            bg=t["bg"], fg=sc,
        ).pack(side="left")
        tk.Label(
            score_frame, text="Neutrality Score", font=("Segoe UI", 9),
            bg=t["bg"], fg=t["text_secondary"],
        ).pack(side="left", padx=(8, 0), pady=(8, 0))

        # Score bar
        bar_frame = tk.Frame(self.window, bg=t["bg"], height=3)
        bar_frame.pack(fill="x", padx=PADDING, pady=(0, 10))
        bar_canvas = tk.Canvas(bar_frame, height=3, bg=t["surface"], highlightthickness=0)
        bar_canvas.pack(fill="x")
        bar_canvas.update_idletasks()
        bar_w = bar_canvas.winfo_width() or 360
        fill_w = int(bar_w * score / 10)
        bar_canvas.create_rectangle(0, 0, fill_w, 3, fill=sc, outline="")

        # Emotional Tone badge
        tone = result.get("emotional_tone", "Unknown")
        tone_frame = tk.Frame(self.window, bg=t["bg"])
        tone_frame.pack(fill="x", padx=PADDING, pady=(0, 10))
        badge = tk.Label(
            tone_frame, text=f" {tone} ", font=("Segoe UI", 9),
            bg=t["badge_bg"], fg=t["badge_fg"], padx=10, pady=3,
        )
        badge.pack(side="left")

        # Likely Intent card
        self._section(
            "Likely Intent",
            result.get("likely_intent", ""),
            on_clarify=clarify,
        )

        # What They Probably Mean
        self._section(
            "What They Probably Mean",
            result.get("what_they_probably_mean", ""),
            on_clarify=clarify,
        )

        # Reassurance callout
        reassurance_frame = tk.Frame(
            self.window, bg=t["reassurance_bg"],
            highlightbackground=t["reassurance_border"], highlightthickness=1,
        )
        reassurance_frame.pack(fill="x", padx=PADDING, pady=(0, 10))
        selectable_text(
            reassurance_frame, result.get("reassurance", ""),
            font=("Segoe UI", 9), bg=t["reassurance_bg"], fg=t["success"],
            width_pixels=POPUP_WIDTH - PADDING * 3, padx=12, pady=12,
            on_clarify=clarify,
        ).pack(fill="x")

        # Suggested Responses
        responses = result.get("suggested_responses", [])
        if responses:
            tk.Label(
                self.window, text="Suggested Responses", font=("Segoe UI", 9, "bold"),
                bg=t["bg"], fg=t["text_secondary"], anchor="w",
            ).pack(fill="x", padx=PADDING, pady=(0, 6))
            for resp in responses:
                self._response_button(resp)

        # Footer
        footer = tk.Frame(self.window, bg=t["bg"])
        footer.pack(fill="x", padx=PADDING, pady=(10, PADDING))
        copy_btn = tk.Label(
            footer, text="Copy All", font=("Segoe UI", 9),
            bg=t["surface"], fg=t["accent"], cursor="hand2",
            padx=10, pady=5,
            highlightbackground=t["border"], highlightthickness=1,
        )
        copy_btn.pack(side="left")
        copy_btn.bind("<Button-1>", lambda e: self._copy_all(result))

        # Position and size the window
        self._position_window(x, y)

        # Bindings to dismiss
        self.window.bind("<Escape>", lambda e: self.close())
        self.window.bind("<FocusOut>", self._on_focus_out)

    def show_clarification(self, text: str, x: int = 100, y: int = 100):
        """Display a clarification result popup."""
        self._create_window()
        t = self.theme

        # Header
        header = tk.Frame(self.window, bg=t["surface"])
        header.pack(fill="x", padx=PADDING, pady=(PADDING, 10))
        tk.Label(
            header, text="Clarification", font=("Segoe UI", 12, "bold"),
            bg=t["surface"], fg=t["text"],
        ).pack(side="left")
        self._close_button(header, t)

        # Clarification body (selectable, with further Clarify available)
        selectable_text(
            self.window, text, font=("Segoe UI", 10),
            bg=t["bg"], fg=t["text"],
            width_pixels=POPUP_WIDTH - PADDING * 2,
            padx=PADDING, pady=PADDING,
            on_clarify=self._on_clarify_callback,
        ).pack(fill="x")

        # Copy button
        footer = tk.Frame(self.window, bg=t["bg"])
        footer.pack(fill="x", padx=PADDING, pady=(0, PADDING))
        copy_btn = tk.Label(
            footer, text="Copy", font=("Segoe UI", 9),
            bg=t["surface"], fg=t["accent"], cursor="hand2",
            padx=10, pady=5,
            highlightbackground=t["border"], highlightthickness=1,
        )
        copy_btn.pack(side="left")
        copy_btn.bind("<Button-1>", lambda e: pyperclip.copy(text))

        # Position and size the window
        self._position_window(x, y)

        self.window.bind("<Escape>", lambda e: self.close())
        self.window.bind("<FocusOut>", self._on_focus_out)

    def show_error(self, message: str, x: int = 100, y: int = 100):
        """Display an error popup."""
        self._create_window()
        t = self.theme

        # Header
        header = tk.Frame(self.window, bg=t["surface"])
        header.pack(fill="x", padx=PADDING, pady=(PADDING, 10))
        tk.Label(
            header, text="Social Decoder", font=("Segoe UI", 12, "bold"),
            bg=t["surface"], fg=t["text"],
        ).pack(side="left")
        self._close_button(header, t)

        # Error message (selectable for copy/paste)
        selectable_text(
            self.window, message, font=("Segoe UI", 10),
            bg=t["bg"], fg=t["error"],
            width_pixels=POPUP_WIDTH - PADDING * 2,
            padx=PADDING, pady=PADDING,
        ).pack(fill="x")

        # Action links
        actions = tk.Frame(self.window, bg=t["bg"])
        actions.pack(fill="x", padx=PADDING, pady=(0, PADDING))

        if "API key" not in message:
            retry = tk.Label(
                actions, text="Retry", font=("Segoe UI", 9, "underline"),
                bg=t["bg"], fg=t["accent"], cursor="hand2",
            )
            retry.pack(side="left", padx=(0, 12))
            retry.bind("<Button-1>", lambda e: self._retry())

        if "API key" in message or "Settings" in message:
            link = tk.Label(
                actions, text="Open Settings", font=("Segoe UI", 9, "underline"),
                bg=t["bg"], fg=t["accent"], cursor="hand2",
            )
            link.pack(side="left")
            link.bind("<Button-1>", lambda e: self._open_settings())

        # Position and size the window
        self._position_window(x, y)

        self.window.bind("<Escape>", lambda e: self.close())
        self.window.bind("<FocusOut>", self._on_focus_out)

    def show_loading(self, x: int = 100, y: int = 100, message: str = "Decoding..."):
        """Display a loading popup with a gentle pulsing text."""
        self._create_window()
        t = self.theme
        self._loading_label = tk.Label(
            self.window, text=message, font=("Segoe UI", 11),
            bg=t["bg"], fg=t["text"], padx=PADDING * 2, pady=PADDING * 2,
        )
        self._loading_label.pack()
        self._position_window(x, y)
        # Start pulse
        self._pulse_dim = _dim_color(t["text"], t["bg"], 0.6)
        self._pulse_bright = t["text"]
        self._pulse_state = True  # True = bright
        self._start_pulse()

    def _start_pulse(self):
        """Pulse the loading label between bright and dim."""
        if not self.window or not self.window.winfo_exists():
            return
        if not hasattr(self, "_loading_label") or not self._loading_label.winfo_exists():
            return
        self._pulse_state = not self._pulse_state
        color = self._pulse_bright if self._pulse_state else self._pulse_dim
        self._loading_label.configure(fg=color)
        aid = self.window.after(750, self._start_pulse)
        self._after_ids.append(aid)

    def _immediate_close(self):
        """Destroy popup instantly, cancelling all pending animations."""
        self._cancel_afters()
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None

    def _cancel_afters(self):
        """Cancel all pending after() callbacks."""
        if self.window and self.window.winfo_exists():
            for aid in self._after_ids:
                try:
                    self.window.after_cancel(aid)
                except Exception:
                    pass
        self._after_ids.clear()

    def close(self):
        """Fade out and destroy the popup window."""
        if self.window and self.window.winfo_exists():
            self._cancel_afters()
            self._fade_out()
        else:
            self.window = None

    def _fade_in(self, duration_ms=300):
        """Fade the popup window from transparent to opaque."""
        if not self.window or not self.window.winfo_exists():
            return
        steps = 15
        interval = duration_ms // steps
        for i in range(steps + 1):
            alpha = 0.05 + (0.95 * i / steps)
            aid = self.window.after(
                i * interval,
                lambda a=alpha: self._set_alpha(a),
            )
            self._after_ids.append(aid)

    def _fade_out(self, duration_ms=200):
        """Fade window to transparent, then destroy."""
        if not self.window or not self.window.winfo_exists():
            return
        steps = 10
        interval = duration_ms // steps
        for i in range(steps + 1):
            alpha = 1.0 - (i / steps)
            aid = self.window.after(
                i * interval,
                lambda a=alpha: self._set_alpha(a),
            )
            self._after_ids.append(aid)
        # Destroy after fade completes
        aid = self.window.after(duration_ms + 20, self._destroy_window)
        self._after_ids.append(aid)

    def _set_alpha(self, alpha):
        """Safely set window alpha."""
        if self.window and self.window.winfo_exists():
            self.window.attributes("-alpha", alpha)

    def _destroy_window(self):
        """Final destroy after fade-out."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None

    def _on_focus_out(self, event):
        """Close popup only when focus leaves the entire window (not child widgets)."""
        if self.window is None or not self.window.winfo_exists():
            return
        # After a short delay, check if focus went to a child of this popup
        self.window.after(50, self._check_focus)

    def _check_focus(self):
        """Check if focus is still inside the popup; close if not."""
        if self.window is None or not self.window.winfo_exists():
            return
        try:
            focused = self.window.focus_get()
            # If focus is on the popup window itself or any of its children, stay open
            if focused is not None:
                w = focused
                while w is not None:
                    if w == self.window:
                        return  # focus is still inside popup
                    w = getattr(w, "master", None)
        except KeyError:
            pass
        self.close()

    def _position_window(self, x: int, y: int):
        """Update layout, compute size, position on screen, and fade in."""
        self.window.update_idletasks()
        # Let tkinter compute the required height from packed content
        req_w = max(self.window.winfo_reqwidth(), POPUP_WIDTH)
        req_h = self.window.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        px, py = clamp_position(x, y, req_w, req_h, sw, sh)
        self.window.geometry(f"{req_w}x{req_h}+{px}+{py}")
        self._fade_in()

    def _create_window(self):
        """Create the frameless toplevel window."""
        self._immediate_close()  # Kill previous window instantly
        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.configure(bg=self.theme["bg"])
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.05)  # Start nearly transparent
        self.window.resizable(False, False)
        # Start off-screen; _position_window will place it correctly
        self.window.geometry(f"{POPUP_WIDTH}x1+-1000+-1000")

    def _close_button(self, parent, t):
        """Create a close button with hover effect."""
        close_btn = tk.Label(
            parent, text="\u2715", font=("Segoe UI", 12),
            bg=t["surface"], fg=t["text_secondary"], cursor="hand2", padx=8,
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.close())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg=t["text"]))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg=t["text_secondary"]))

    def _section(self, title: str, text: str, bg: str = None, on_clarify=None):
        """Add a titled text section to the popup."""
        t = self.theme
        bg = bg or t["card_bg"]
        frame = tk.Frame(
            self.window, bg=bg,
            highlightbackground=t["border"], highlightthickness=1,
        )
        frame.pack(fill="x", padx=PADDING, pady=(0, 10))
        tk.Label(
            frame, text=title, font=("Segoe UI", 9),
            bg=bg, fg=t["text_secondary"], anchor="w",
        ).pack(fill="x", padx=12, pady=(12, 2))
        selectable_text(
            frame, text, font=("Segoe UI", 9),
            bg=bg, fg=t["text"],
            width_pixels=POPUP_WIDTH - PADDING * 3, padx=12,
            on_clarify=on_clarify,
        ).pack(fill="x", pady=(0, 12))

    def _response_button(self, text: str):
        """Add a clickable suggested response."""
        t = self.theme
        btn = tk.Label(
            self.window, text=text, font=("Segoe UI", 9),
            bg=t["surface"], fg=t["text"], cursor="hand2",
            padx=14, pady=8, wraplength=POPUP_WIDTH - PADDING * 3,
            anchor="w",
            highlightbackground=t["border"], highlightthickness=1,
        )
        btn.pack(fill="x", padx=PADDING, pady=(0, 4))
        btn.bind("<Button-1>", lambda e, txt=text: self._copy_response(txt, btn))
        btn.bind("<Enter>", lambda e: btn.configure(bg=t["surface_hover"]))
        btn.bind("<Leave>", lambda e: btn.configure(bg=t["surface"]))

    def _copy_response(self, text: str, btn: tk.Label):
        """Copy a suggested response to clipboard and show feedback."""
        pyperclip.copy(text)
        original_text = btn.cget("text")
        btn.configure(text="Copied!", fg=self.theme["success"])
        btn.after(1500, lambda: btn.configure(text=original_text, fg=self.theme["text"]))

    def _copy_all(self, result: dict):
        """Copy the full decode result as readable text."""
        lines = [
            f"Neutrality Score: {result.get('neutrality_score', '?')}/10",
            f"Emotional Tone: {result.get('emotional_tone', '?')}",
            f"Likely Intent: {result.get('likely_intent', '')}",
            f"What They Probably Mean: {result.get('what_they_probably_mean', '')}",
            f"Reassurance: {result.get('reassurance', '')}",
        ]
        responses = result.get("suggested_responses", [])
        if responses:
            lines.append("Suggested Responses:")
            for r in responses:
                lines.append(f"  - {r}")
        pyperclip.copy("\n".join(lines))

    def _open_settings(self):
        """Trigger the settings callback."""
        self._immediate_close()
        if self._on_settings_callback:
            self._on_settings_callback()

    def _retry(self):
        """Trigger the retry callback."""
        self._immediate_close()
        if self._on_retry_callback:
            self._on_retry_callback()
