"""History browser window."""
import json
import tkinter as tk
from theme import get_theme, score_color
from widgets import selectable_text


class HistoryWindow:
    """Scrollable history browser for past decodes."""

    def __init__(self, root: tk.Tk, history_db, theme_name: str = "dark"):
        self.root = root
        self.db = history_db
        self.theme = get_theme(theme_name)
        self._build()

    def _build(self):
        t = self.theme
        self.window = tk.Toplevel(self.root)
        self.window.title("Social Decoder - History")
        self.window.configure(bg=t["bg"])
        self.window.geometry("520x600")

        # Center on screen
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - 520) // 2
        y = (sh - 600) // 2
        self.window.geometry(f"+{x}+{y}")

        # Header with search
        header = tk.Frame(self.window, bg=t["bg"])
        header.pack(fill="x", padx=20, pady=(20, 8))

        tk.Label(
            header, text="History", font=("Segoe UI", 14, "bold"),
            bg=t["bg"], fg=t["text"],
        ).pack(side="left")

        clear_btn = tk.Label(
            header, text="Clear All", font=("Segoe UI", 9),
            bg=t["surface"], fg=t["error"], cursor="hand2",
            padx=10, pady=5,
            highlightbackground=t["border"], highlightthickness=1,
        )
        clear_btn.pack(side="right")
        clear_btn.bind("<Button-1>", lambda e: self._confirm_clear())

        # Search bar
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._refresh())
        search = tk.Entry(
            self.window, textvariable=self.search_var, font=("Segoe UI", 10),
            bg=t["surface"], fg=t["text"], insertbackground=t["text"],
            relief="flat", bd=0,
            highlightbackground=t["border"], highlightthickness=1,
        )
        search.pack(fill="x", padx=20, pady=(0, 8), ipady=6)
        search.insert(0, "")
        search.configure(validate="none")

        # Scrollable list
        container = tk.Frame(self.window, bg=t["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        canvas = tk.Canvas(container, bg=t["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg=t["bg"])

        self.list_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw", width=480)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-e.delta // 120, "units"))
        self.list_frame.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-e.delta // 120, "units"))

        self._refresh()

    def _refresh(self):
        """Reload the list from the database."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().strip() if hasattr(self, "search_var") else ""
        entries = self.db.search(query) if query else self.db.get_all()

        t = self.theme
        if not entries:
            tk.Label(
                self.list_frame, text="No history yet", font=("Segoe UI", 10),
                bg=t["bg"], fg=t["text_secondary"],
            ).pack(pady=20)
            return

        for entry in entries:
            self._add_entry_row(entry)

    def _add_entry_row(self, entry: dict):
        """Add a single history entry row."""
        t = self.theme
        row = tk.Frame(self.list_frame, bg=t["surface"], cursor="hand2")
        row.pack(fill="x", pady=(0, 4))

        score = entry.get("neutrality_score", 5)
        sc = score_color(score, t)
        dot = tk.Canvas(row, width=12, height=12, bg=t["surface"], highlightthickness=0)
        dot.pack(side="left", padx=(10, 6), pady=10)
        dot.create_oval(2, 2, 10, 10, fill=sc, outline="")

        text = entry.get("original_text", "")
        preview = text[:50] + ("..." if len(text) > 50 else "")
        tk.Label(
            row, text=preview, font=("Segoe UI", 9),
            bg=t["surface"], fg=t["text"], anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)

        ts = entry.get("timestamp", "")
        tk.Label(
            row, text=str(ts)[:16], font=("Segoe UI", 8),
            bg=t["surface"], fg=t["text_secondary"],
        ).pack(side="right", padx=(0, 10), pady=10)

        row_id = entry.get("id")
        children = list(row.winfo_children())

        def on_enter(e, r=row, ch=children):
            r.configure(bg=t["surface_hover"])
            for c in ch:
                if isinstance(c, tk.Label):
                    c.configure(bg=t["surface_hover"])

        def on_leave(e, r=row, ch=children):
            r.configure(bg=t["surface"])
            for c in ch:
                if isinstance(c, tk.Label):
                    c.configure(bg=t["surface"])

        for widget in [row] + children:
            widget.bind("<Button-1>", lambda e, rid=row_id: self._show_detail(rid))
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def _show_detail(self, row_id: int):
        """Show full decode detail in a sub-window."""
        entry = self.db.get_by_id(row_id)
        if not entry:
            return

        t = self.theme
        detail = tk.Toplevel(self.window)
        detail.title("Decode Detail")
        detail.configure(bg=t["bg"])
        detail.geometry("440x500")

        try:
            data = json.loads(entry.get("full_response", "{}"))
        except json.JSONDecodeError:
            data = {}

        tk.Label(
            detail, text="Original Message", font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["text_secondary"], anchor="w",
        ).pack(fill="x", padx=20, pady=(20, 4))

        selectable_text(
            detail, entry.get("original_text", ""), font=("Segoe UI", 10),
            bg=t["surface"], fg=t["text"], width_pixels=400, padx=8, pady=8,
        ).pack(fill="x", padx=20, pady=(0, 8))

        score = entry.get("neutrality_score", 5)
        sc = score_color(score, t)
        tk.Label(
            detail, text=f"Neutrality Score: {score}/10", font=("Segoe UI", 12, "bold"),
            bg=t["bg"], fg=sc,
        ).pack(fill="x", padx=20, pady=(0, 8))

        for key, label in [
            ("likely_intent", "Likely Intent"),
            ("what_they_probably_mean", "What They Probably Mean"),
            ("reassurance", "Reassurance"),
        ]:
            val = data.get(key, entry.get(key, ""))
            if val:
                tk.Label(
                    detail, text=label, font=("Segoe UI", 9, "bold"),
                    bg=t["bg"], fg=t["text_secondary"], anchor="w",
                ).pack(fill="x", padx=20, pady=(4, 2))
                selectable_text(
                    detail, val, font=("Segoe UI", 9),
                    bg=t["bg"], fg=t["text"], width_pixels=400,
                ).pack(fill="x", padx=20, pady=(0, 4))

    def _confirm_clear(self):
        """Show confirmation before clearing history."""
        t = self.theme
        confirm = tk.Toplevel(self.window)
        confirm.title("Clear History")
        confirm.configure(bg=t["bg"])
        confirm.geometry("300x120")
        confirm.grab_set()

        tk.Label(
            confirm, text="Delete all history?", font=("Segoe UI", 11),
            bg=t["bg"], fg=t["text"],
        ).pack(pady=(20, 12))

        btn_row = tk.Frame(confirm, bg=t["bg"])
        btn_row.pack()

        cancel = tk.Label(
            btn_row, text="Cancel", font=("Segoe UI", 10),
            bg=t["surface"], fg=t["text"], cursor="hand2", padx=12, pady=6,
        )
        cancel.pack(side="left", padx=(0, 8))
        cancel.bind("<Button-1>", lambda e: confirm.destroy())

        delete = tk.Label(
            btn_row, text="Delete", font=("Segoe UI", 10, "bold"),
            bg=t["error"], fg="#ffffff", cursor="hand2", padx=12, pady=6,
        )
        delete.pack(side="left")
        delete.bind("<Button-1>", lambda e: (self.db.clear_all(), confirm.destroy(), self._refresh()))
