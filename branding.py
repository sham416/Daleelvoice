"""Brand assets for Mubarak Bin Mohammed Charter School.

Centralizing brand details here so any tweak (color, font file path,
school name) only needs to happen in one place. Follows the Charter
Schools Visual Identity Guidelines:

  - Navy (#04045C) must appear in every deliverable as the main color.
  - Exactly ONE accent color per visual — never two. We picked teal.
  - English font: Gopher (display in Black/Bold, body in Regular/Medium).
  - Backgrounds are never black.
"""

from __future__ import annotations

import base64
from pathlib import Path

# --- Identity --------------------------------------------------------
SCHOOL_NAME_EN = "Mubarak Bin Mohammed Charter School"
SCHOOL_NAME_AR = "مدرسة مبارك بن محمد للشراكات التعليمية"
APP_NAME = "Lesson Voice Analyzer"

# --- Colors (from the Charter Schools brand palette) -----------------
NAVY = "#04045C"          # main brand color — must be present in every visual
TEAL = "#00B3BC"          # accent (the only one we use)
RED = "#FF0B53"           # available but NOT used here — would violate
YELLOW = "#FFBA00"        # the one-accent rule

# Supporting neutrals (not from the brand but compatible)
SOFT_BG = "#F5F7FA"
INK = "#04045C"           # text color = navy per guidelines
MUTED = "#5A5A78"         # for caption / disclaimer rows

# --- Paths -----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / "assets"
FONTS = ASSETS / "fonts"
LOGO_WHITE = ASSETS / "logo_white.png"      # transparent bg, white logo
LOGO_NAVY = ASSETS / "logo_navy.png"        # pre-baked white logo on navy


# --- Font loading ----------------------------------------------------
def _b64_font(path: Path) -> str:
    """Read a font file and return base64 (used to inline in CSS)."""
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def gopher_font_css() -> str:
    """Return a <style> block that registers Gopher via @font-face.

    Embeds the OTF files as base64 so the font works in Streamlit
    without a separate static-file server. Falls back gracefully if a
    file is missing.
    """
    weights = [
        ("Gopher", 400, "normal", FONTS / "Gopher-Regular.ttf"),
        ("Gopher", 500, "normal", FONTS / "Gopher-Medium.ttf"),
        ("Gopher", 700, "normal", FONTS / "Gopher-Bold.ttf"),
        ("Gopher", 900, "normal", FONTS / "Gopher-Black.ttf"),
    ]
    face_blocks: list[str] = []
    for family, weight, style, path in weights:
        b64 = _b64_font(path)
        if not b64:
            continue
        face_blocks.append(
            f"""@font-face {{
              font-family: '{family}';
              font-weight: {weight};
              font-style: {style};
              src: url(data:font/ttf;base64,{b64}) format('truetype');
              font-display: swap;
            }}"""
        )
    if not face_blocks:
        return ""

    overrides = """
    html, body, [class*="css"], .stMarkdown, .stTextInput, .stTextArea,
    .stSelectbox, .stButton, .stNumberInput, .stDateInput,
    .stMetric, h1, h2, h3, h4, h5, h6, p, span, div, label, button {
      font-family: 'Gopher', system-ui, -apple-system, sans-serif !important;
    }
    h1, h2, h3 { font-weight: 700; letter-spacing: -0.01em; }
    h1 { color: #04045C; }
    """
    return "<style>\n" + "\n".join(face_blocks) + "\n" + overrides + "\n</style>"


def logo_navy_data_uri() -> str:
    """Return the navy-bg logo as a data: URI for inline HTML/CSS use."""
    if not LOGO_NAVY.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(LOGO_NAVY.read_bytes()).decode("ascii")
