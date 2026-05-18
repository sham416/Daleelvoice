# Brand application notes

This app is branded for **Mubarak Bin Mohammed Charter School** per
the Charter Schools Visual Identity Guidelines.

## What's applied

| Element       | Choice                                                |
|---------------|-------------------------------------------------------|
| Main color    | Navy `#04045C` — appears on every screen and PDF page |
| Accent color  | Teal `#00B3BC` — single accent, never combined with red or yellow |
| English font  | Gopher (Regular, Medium, Bold, Black) — in `assets/fonts/` |
| Logo          | White-on-transparent PNG in `assets/logo_white.png`; navy-on-bar version in `assets/logo_navy.png` |

## What's deliberately NOT applied

These are brand elements that exist in the guidelines but didn't fit
a coaching tool and would have hurt usability:

- The diamond NUQTA pattern — beautiful for posters, busy as a UI
  background. Skipped.
- Gradient backgrounds — guideline says digital only, but reduce text
  contrast in a long-form report. Skipped in favor of clean white.
- Pink/yellow accents — guideline forbids combining two accents per
  visual, so the app commits to teal across every screen.
- Arabic body text — the app is built for English-speaking instructional
  coaches reading the report. The Arabic school name appears in the
  logo and could be added to headers if needed (Graphik Arabic would
  need to be added to `assets/fonts/` first).

## Files I changed for the brand

- `branding.py` — new — single source of truth for colors, fonts, logo
- `.streamlit/config.toml` — new — Streamlit primary/text colors set to navy
- `report.py` — header bar, footer, Gopher registration, navy palette
- `app.py` — logo in sidebar, Gopher CSS, removed emoji from headings
- `assets/` — new folder with logo and 4 Gopher TTF weights

## If you want to swap the accent color later

Open `branding.py` and change `TEAL = "#00B3BC"` to `RED = "#FF0B53"`
or `YELLOW = "#FFBA00"` — then everywhere `branding.TEAL` is used in
the code, swap it. One file, three or four lines. Don't introduce a
second accent without removing the first; the guideline is firm on
this.

## If you want Arabic font support

1. Get the Graphik Arabic font files (TTF format).
2. Drop them in `assets/fonts/` named `GraphikArabic-Regular.ttf`,
   `GraphikArabic-Bold.ttf`, etc.
3. In `report.py`, register them next to Gopher; in `branding.py`,
   extend `gopher_font_css()` to add `@font-face` rules for them
   with `unicode-range: U+0600-06FF` to scope to Arabic.

## Brand rules respected

- ✅ Logo never appears next to the ADEK or operator logo.
- ✅ Logo not rotated, stretched, recolored, or otherwise altered.
- ✅ Navy is present on every page.
- ✅ Only one accent color (teal) — never paired with another.
- ✅ Brand fonts used (Gopher) with Helvetica fallback only if the
  font files are missing.
- ✅ Background is never black (uses white with a small navy header).
