"""Shared UI widgets for Social Decoder."""
import tkinter as tk
import math
import pyperclip


def selectable_text(parent, text, font=("Segoe UI", 9), bg="#1e1e1e", fg="#ffffff",
                    width_pixels=380, padx=0, pady=0, justify="left",
                    on_clarify=None):
    """Read-only Text widget that looks like a Label but allows text selection and copy.

    Args:
        parent: Parent tkinter widget.
        text: The text to display.
        font: Font tuple.
        bg: Background color.
        fg: Foreground color.
        width_pixels: Approximate pixel width for line-height estimation.
        padx: Internal horizontal padding.
        pady: Internal vertical padding.
        justify: Text alignment ("left", "center", "right").
        on_clarify: Optional callback(selected_text) for the Clarify right-click option.

    Returns:
        A configured tk.Text widget (already has text inserted, state=disabled).
    """
    w = tk.Text(
        parent, font=font, bg=bg, fg=fg, relief="flat", bd=0,
        wrap="word", highlightthickness=0, cursor="ibeam",
        padx=padx, pady=pady,
    )

    # Set alignment tag
    if justify == "center":
        w.tag_configure("align", justify="center")
    elif justify == "right":
        w.tag_configure("align", justify="right")
    else:
        w.tag_configure("align", justify="left")

    w.insert("1.0", text, "align")
    w.configure(state="disabled")

    # Estimate height in lines based on text length and available width
    font_size = font[1] if len(font) > 1 and isinstance(font[1], int) else 9
    avg_char_width = max(font_size * 0.78, 5)
    usable_width = max(width_pixels - padx * 2, 60)
    chars_per_line = max(int(usable_width / avg_char_width), 10)

    num_lines = 0
    for line in text.split("\n"):
        num_lines += max(1, math.ceil((len(line) or 1) / chars_per_line))
    w.configure(height=num_lines)

    # Right-click context menu
    _attach_context_menu(w, on_clarify)

    return w


def _attach_context_menu(text_widget, on_clarify=None):
    """Attach a right-click context menu with Copy (and optionally Clarify) to a Text widget."""

    def _get_selected(w):
        """Get selected text from the Text widget, or all text if nothing selected."""
        try:
            return w.get("sel.first", "sel.last")
        except tk.TclError:
            return None

    def _on_copy(w):
        sel = _get_selected(w)
        if sel:
            pyperclip.copy(sel)

    def _on_clarify(w, callback):
        sel = _get_selected(w)
        if not sel:
            # If nothing selected, use all text in the widget
            sel = w.get("1.0", "end-1c").strip()
        if sel and callback:
            callback(sel)

    def _show_menu(event):
        w = event.widget
        menu = tk.Menu(w, tearoff=0)

        has_selection = False
        try:
            w.get("sel.first", "sel.last")
            has_selection = True
        except tk.TclError:
            pass

        menu.add_command(
            label="Copy",
            command=lambda: _on_copy(w),
            state="normal" if has_selection else "disabled",
        )

        if on_clarify is not None:
            menu.add_separator()
            label = "Clarify Selection" if has_selection else "Clarify All"
            menu.add_command(
                label=label,
                command=lambda: _on_clarify(w, on_clarify),
            )

        menu.tk_popup(event.x_root, event.y_root)

    text_widget.bind("<Button-3>", _show_menu)
