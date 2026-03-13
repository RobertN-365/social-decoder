"""Color constants and shared styling for dark/light themes."""

# Dark theme (default) — Sage & Lavender palette
DARK = {
    "bg": "#1a1f2e",
    "surface": "#232a3b",
    "surface_hover": "#2a3348",
    "text": "#e0dfe6",
    "text_secondary": "#9b97a8",
    "accent": "#8b9dc3",
    "border": "#2f3547",
    "success": "#7eb89c",
    "warning": "#d4b896",
    "error": "#c48b8b",
    "score_low": "#c48b8b",      # 1-3: dusty rose
    "score_mid_low": "#d4b896",  # 4-5: warm amber
    "score_mid": "#d4c878",      # 6: soft gold
    "score_mid_high": "#a3c49b", # 7-8: sage
    "score_high": "#7eb89c",     # 9-10: mint sage
    "reassurance_bg": "#1e2a28",
    "reassurance_border": "#2a3d38",
    "card_bg": "#262d3e",
    "badge_bg": "#2d3552",
    "badge_fg": "#b8c4e0",
}

# Light theme — Sage & Lavender palette
LIGHT = {
    "bg": "#f5f3f0",
    "surface": "#ffffff",
    "surface_hover": "#eeece8",
    "text": "#3a3548",
    "text_secondary": "#7a7488",
    "accent": "#6b7fa3",
    "border": "#e0ddd8",
    "success": "#5a9a78",
    "warning": "#b89a6e",
    "error": "#a87070",
    "score_low": "#a87070",
    "score_mid_low": "#b89a6e",
    "score_mid": "#b8a840",
    "score_mid_high": "#7a9e72",
    "score_high": "#5a9a78",
    "reassurance_bg": "#eef5f0",
    "reassurance_border": "#c8dece",
    "card_bg": "#f0eeeb",
    "badge_bg": "#e8e4f0",
    "badge_fg": "#5a5070",
}

THEMES = {"dark": DARK, "light": LIGHT}


def get_theme(name: str = "dark") -> dict:
    """Return a theme dict by name. Defaults to dark."""
    return THEMES.get(name, DARK)


def score_color(score: int, theme: dict) -> str:
    """Return the color for a given neutrality score (1-10)."""
    if score <= 3:
        return theme["score_low"]
    if score <= 5:
        return theme["score_mid_low"]
    if score <= 6:
        return theme["score_mid"]
    if score <= 8:
        return theme["score_mid_high"]
    return theme["score_high"]
