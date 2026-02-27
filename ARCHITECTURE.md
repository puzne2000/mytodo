# MyTodo — Architecture

## Overview

A desktop todo app built with Python 3 and PySide6 (Qt). Lists are displayed as tabs; each list contains plain-text items that can be edited, reordered by drag-and-drop, and promoted to the top with a double-click. All mutations are undoable with Ctrl+Z. State is persisted to a TOML file on disk.

## Running

```bash
python3 main.py
```

Data is saved automatically to `~/.mytodo.toml` when the window closes.

---

## File Map

```
mytodo/
├── main.py            # Entry point
├── window.py          # Main window (QTabWidget, toolbar, tab bar)
├── list_widget.py     # Per-list widget (drag-drop, item management)
├── item_widget.py     # Single item row (hot zone + text editor)
├── undo_commands.py   # QUndoCommand subclasses for every operation
├── data.py            # In-memory data model (pure Python dataclasses)
├── storage.py         # TOML serialisation / deserialisation
├── style.py           # Visual constants (colours, dimensions, animation params)
└── ARCHITECTURE.md    # This file
```

---

## Files in Detail

### `main.py`
Creates the `QApplication`, sets the Fusion style, instantiates `MainWindow`, and starts the event loop. No logic lives here.

---

### `data.py` — Data Model
Pure Python dataclasses; no Qt dependency. Used as the canonical source of truth when loading and saving.

```
AppData
└── lists: list[TodoList]
    ├── name: str
    └── items: list[str]
```

`AppData` methods: `add_list`, `move_list_to_front`, `move_item_to_top`, `move_item`.
These are used only during load/save; the live UI state is held in the Qt widgets themselves and synced back to `AppData` at close time.

---

### `storage.py` — Persistence
Reads and writes `~/.mytodo.toml` using:
- `tomllib` (Python 3.11+ stdlib) for reading
- `tomli_w` (third-party, pip) for writing

**File format:**
```toml
[[lists]]
name = "Work"
items = ["Write report", "Schedule meeting"]

[[lists]]
name = "Personal"
items = ["Buy groceries"]
```

`load(path) -> AppData` — returns an empty `AppData` if the file does not exist.
`save(app, path)` — overwrites the file with current state.

---

### `style.py` — Visual Constants

Single source of truth for all appearance decisions. Import and edit here to change how the app looks without touching widget code.

| Constant | What it controls |
|---|---|
| `ITEM_HOT_ZONE_WIDTH` | Width of the blue strip on each item |
| `ITEM_HOT_ZONE_COLOR` / `_HOVER_COLOR` | Hot zone colours |
| `ITEM_EDIT_FOCUS_BG` / `_BORDER` | Text editor highlight when focused |
| `LIST_BG`, `ITEM_BG`, `ITEM_BORDER` | List and item background/border colours |
| `ITEM_SELECTED_BG` / `_BORDER` | Selected item background and border colour |
| `ITEM_SELECTED_BORDER_WIDTH` | Border width (px) of the selected item ring |
| `TAB_HOT_ZONE_WIDTH` | Width of the promote zone on each tab |
| `TAB_RENAME_BORDER` | Border colour of the inline rename editor |
| `FLASH_COLOR` | Starting colour of the tab drop-flash overlay |
| `FLASH_DURATION_MS` | How long the flash fade takes (milliseconds) |
| `FLASH_EASING` | Animation easing curve (`QEasingCurve.Type`) |

---

### `item_widget.py` — Single Item Row

Each todo item is rendered as an `ItemWidget`:

```
ItemWidget (QWidget, horizontal layout)
├── HotZone (QFrame, width from style.py)   ← double-click → promote to top
│                                             ← drag → move to another list
└── ItemTextEdit (QTextEdit)                 ← click to edit in place
```

**`HotZone`** — a narrow blue strip on the left.
- `mouseDoubleClickEvent` → emits `double_clicked` (promote to top).
- `mousePressEvent` / `mouseMoveEvent` → detects drag threshold and emits `drag_requested`. Returns immediately after emitting to avoid use-after-free if the widget is deleted during the drag.

**`ItemTextEdit`** — a plain-text, auto-resizing editor.
- On `focusIn`: records `_original_text` and emits `editing_started`.
- On `focusOut`: if text changed, emits `editing_finished(new_text)`.
- `keyPressEvent`: Escape → emits `escape_pressed`; Cmd+Down/Up → emits `navigate_requested(±1)`.
- Height adjusts automatically as content grows.

**`ItemWidget`** — assembles the two above and exposes:
- `promote_requested` signal → wired to `TodoListWidget._on_promote`
- `edit_committed(old, new)` signal → wired to `TodoListWidget._on_edit`
- `drag_requested` signal → wired to `TodoListWidget._start_hot_zone_drag`
- `item_focused` signal → wired to `TodoListWidget.setCurrentItem` (keeps list selection in sync with the text editor that has focus)
- `editing_cancelled` signal → wired to `TodoListWidget.setFocus` (Escape exits edit mode)
- `navigate_requested(±1)` signal → wired to `TodoListWidget._navigate_edit`
- `text()` / `set_text()` accessors
- `set_selected(bool)` — called by `TodoListWidget._on_selection_changed` to show/hide the selection border ring. Internally sets `_selected` and triggers a repaint.
- `paintEvent` — draws a rounded-rect border using `ITEM_SELECTED_BORDER` / `ITEM_SELECTED_BORDER_WIDTH` from `style.py` when `_selected` is True. The pen is inset by half its width so it stays within the widget boundary.

---

### `list_widget.py` — Per-List Widget

`TodoListWidget(QListWidget)` holds the items for one tab.

**Item storage:** each `QListWidgetItem` stores the item's plain text in `Qt.ItemDataRole.UserRole`. The associated `ItemWidget` is set via `setItemWidget`. The UserRole copy is kept in sync with live edits (used by drag-and-drop MIME payload and `all_texts()`).

**Drag-and-drop:** uses a custom MIME type `application/x-mytodo-item` with payload `"<widget_id>|<from_index>|<text>"`.
- Same-list drop (from anywhere on the item) → pushes `ReorderItemCommand` directly.
- Cross-list drop via hot zone drag → `_start_hot_zone_drag` builds the MIME payload and starts a `QDrag`. The drop is handled by `HotTabBar` (see below), not by the list widget itself.

**Row moves:** `_move_row(from, to)` takes the item out, creates a fresh `QListWidgetItem` at the target position, and rebuilds the `ItemWidget`. This is necessary because Qt detaches widget bindings on `takeItem`.

**Keyboard handling** (`keyPressEvent`):
- Enter → start editing the current item (focus its `ItemTextEdit`).
- Escape → deselect current item (`setCurrentItem(None)`).
- Cmd+Backspace (item selected, not editing) → push `DeleteItemCommand`; after deletion selects the item below, or the new last item if the deleted item was last, or focuses the list if it was the only item.
- Up (on row 0, not editing) → deselect current item.
- Up (no item selected) → swallowed; nothing happens.
- Down (no item selected) → Qt default selects the first item.
- Left / Right (no item selected) → emit `navigate_tab_requested(±1)`.

`_navigate_edit(item, delta)` commits the active edit and moves focus to the adjacent item, or returns focus to the list at the boundary.

**Selection border:** `currentItemChanged` is connected to `_on_selection_changed`, which calls `set_selected(True/False)` on the affected `ItemWidget`s. Switching tabs clears selection via `window._on_tab_changed`.

**Signals:**
- `cross_list_drop_received(dest_index, text)` / `cross_list_drop_sent(src_index)` — cross-list drag
- `navigate_tab_requested(delta)` — emitted when Left/Right pressed with no item selected; handled by `MainWindow._on_navigate_tab`

**Public API** (called by undo commands):
`set_item_text`, `move_item_to_top`, `move_item_from_top`, `reorder_item`, `append_item`, `remove_last_item`, `remove_item`, `insert_item`, `all_texts`

---

### `window.py` — Main Window

**`HotTabBar(QTabBar)`** — custom tab bar with two double-click zones and drop support:
- Left N px (from `style.TAB_HOT_ZONE_WIDTH`) → emits `tab_promoted(index)` → moves list to the leftmost position
- Remainder → emits `tab_rename_requested(index)` → opens an inline `QLineEdit` over the tab label
- Accepts `application/x-mytodo-item` drops → emits `item_dropped_on_tab(tab_index, payload)` → `MainWindow` moves the item to position 0 of the target list and calls `flash_tab(index)`

**Flash animation** (`flash_tab`, `_update_flash`, `_clear_flash`, `paintEvent`): a `QVariantAnimation` interpolates `FLASH_COLOR` → transparent over `FLASH_DURATION_MS` ms. The current colour per tab is stored in `_flash_colors: dict[int, QColor]` and painted as a semi-transparent overlay on top of the normal tab bar in `paintEvent`. All animation parameters live in `style.py`.

**`MainWindow(QMainWindow)`** layout:
```
QMainWindow
└── central QWidget (QVBoxLayout)
    ├── toolbar (QHBoxLayout)
    │   ├── "+ New list" button
    │   ├── "+ New item" button
    │   └── "Delete item" button
    └── QTabWidget (with HotTabBar)
        └── TodoListWidget  ×  n
```

Key responsibilities:
- Owns the single `QUndoStack` shared across all list widgets.
- Wires Ctrl+Z / Ctrl+Shift+Z and Cmd+S shortcuts to undo and save.
- Handles cross-list drag-drop by finding the source list and pushing `MoveItemBetweenListsCommand`.
- `_save()` syncs widget state into `AppData` and writes to disk; called by both Cmd+S and `closeEvent`.
- `_on_tab_changed(index)` — clears item selection in the newly active list and posts `QTimer.singleShot(0, lw.setFocus)` to give focus to the `TodoListWidget` after Qt's own focus restoration runs (prevents Qt from restoring focus to an `ItemTextEdit` and silently entering edit mode).
- `_on_navigate_tab(delta)` — moves to the adjacent tab (clamped to valid range) in response to `navigate_tab_requested` from the active list widget.
- `_on_delete_item()` — if an item is selected, pushes `DeleteItemCommand`; if no item is selected and the list is empty, pushes `DeleteListCommand`; does nothing if the list has items but none is selected.

**Public API** (called by undo commands):
`move_tab_to_front(from, to)`, `rename_tab(index, new_name)`, `remove_tab(index)`, `insert_tab(index, name)`, `transfer_item(from_list, from_item, to_list, to_item, text)`

---

### `undo_commands.py` — Undo Stack

All operations are reversible via `QUndoCommand` subclasses pushed onto the shared `QUndoStack`. Each command stores enough state to fully redo and undo the operation.

| Command | Redo | Undo |
|---|---|---|
| `EditItemCommand` | set item text to new | set item text to old |
| `MoveItemToTopCommand` | move item to index 0 | move item back to original index |
| `ReorderItemCommand` | move from → to | move to → from |
| `MoveItemBetweenListsCommand` | remove from src, insert at dst | remove from dst, insert at src |
| `MoveListToFrontCommand` | move tab to index 0 | move tab back to original index |
| `RenameTabCommand` | set tab text to new name | set tab text to old name |
| `AddItemCommand` | append blank item | remove last item |
| `DeleteItemCommand` | remove item at index | re-insert item at index with saved text |
| `DeleteListCommand` | remove tab at index | re-insert empty tab at index with saved name |

---

## Keyboard Shortcuts

| Shortcut | Context | Action |
|---|---|---|
| Cmd+Z | anywhere | Undo |
| Cmd+Shift+Z | anywhere | Redo |
| Cmd+S | anywhere | Save to disk immediately |
| Enter | list focused, item selected | Start editing the selected item |
| Escape | editing an item | Commit edit, return focus to list |
| Escape | item selected, not editing | Deselect item |
| Cmd+Down | editing an item | Commit edit, move to item below |
| Cmd+Up | editing an item | Commit edit, move to item above |
| Up | first item selected, not editing | Deselect item |
| Up | no item selected | No-op |
| Down | no item selected | Select first item |
| Cmd+Backspace | item selected, not editing | Delete selected item |
| Left | no item selected | Navigate to previous list |
| Right | no item selected | Navigate to next list |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `PySide6` | 6.10+ | Qt GUI framework |
| `tomli_w` | 1.2+ | Write TOML files |
| `tomllib` | stdlib (3.11+) | Read TOML files |

---

## Branch notes

`cross-list-drag` has been merged into `main`. All features are on `main`.
