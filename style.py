"""Visual style constants — edit here to tweak the app's appearance."""

from PySide6.QtGui import QColor
from PySide6.QtCore import QEasingCurve

# ── Item hot zone ─────────────────────────────────────────────────────────────
ITEM_HOT_ZONE_WIDTH = 16          # px wide strip on the left of each item
ITEM_HOT_ZONE_COLOR = "#b0c4de"
ITEM_HOT_ZONE_HOVER_COLOR = "#4682b4"

# ── Item text editor ──────────────────────────────────────────────────────────
ITEM_EDIT_FOCUS_BG = "#fffde7"
ITEM_EDIT_FOCUS_BORDER = "#aaa"

# ── List widget ───────────────────────────────────────────────────────────────
LIST_BG = "#f5f5f5"
ITEM_BG = "white"
ITEM_BORDER = "#ddd"
ITEM_SELECTED_BG = "#e3f2fd"
ITEM_SELECTED_BORDER = "#90caf9"
ITEM_SELECTED_BORDER_WIDTH = 2

# ── Tab bar ───────────────────────────────────────────────────────────────────
TAB_HOT_ZONE_WIDTH = 18           # px from left edge of tab → promote-to-front zone
TAB_RENAME_BORDER = "#4682b4"

# ── Cross-list drop flash animation ──────────────────────────────────────────
FLASH_COLOR = QColor(100, 180, 255, 180)   # semi-transparent blue overlay
FLASH_DURATION_MS = 1200                    # total fade-out duration
FLASH_EASING = QEasingCurve.Type.OutCubic  # starts fast, decelerates
