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

### `item_widget.py` — Single Item Row

Each todo item is rendered as an `ItemWidget`:

```
ItemWidget (QWidget, horizontal layout)
├── HotZone (QFrame, 16 px wide)   ← double-click → promote to top
└── ItemTextEdit (QTextEdit)        ← click to edit in place
```

**`HotZone`** — a narrow blue strip on the left. `mouseDoubleClickEvent` emits `double_clicked`.

**`ItemTextEdit`** — a plain-text, auto-resizing editor.
- On `focusIn`: records `_original_text` and emits `editing_started`.
- On `focusOut`: if text changed, emits `editing_finished(new_text)`.
- Height adjusts automatically as content grows.

**`ItemWidget`** — assembles the two above and exposes:
- `promote_requested` signal → wired to `TodoListWidget._on_promote`
- `edit_committed(old, new)` signal → wired to `TodoListWidget._on_edit`
- `text()` / `set_text()` accessors

---

### `list_widget.py` — Per-List Widget

`TodoListWidget(QListWidget)` holds the items for one tab.

**Item storage:** each `QListWidgetItem` stores the item's plain text in `Qt.ItemDataRole.UserRole`. The associated `ItemWidget` is set via `setItemWidget`. The UserRole copy is kept in sync with live edits (used by drag-and-drop MIME payload and `all_texts()`).

**Drag-and-drop:** uses a custom MIME type `application/x-mytodo-item` with payload `"<widget_id>|<from_index>|<text>"`.
- Same-list drop → pushes `ReorderItemCommand` directly.
- Cross-list drop → emits `cross_list_drop_received(to_index, text)`; `MainWindow` handles the undo command.

**Row moves:** `_move_row(from, to)` takes the item out, creates a fresh `QListWidgetItem` at the target position, and rebuilds the `ItemWidget`. This is necessary because Qt detaches widget bindings on `takeItem`.

**Public API** (called by undo commands):
`set_item_text`, `move_item_to_top`, `move_item_from_top`, `reorder_item`, `append_item`, `remove_last_item`, `remove_item`, `insert_item`, `all_texts`

---

### `window.py` — Main Window

**`HotTabBar(QTabBar)`** — custom tab bar with two double-click zones per tab:
- Left 18 px → emits `tab_promoted(index)` → moves list to the leftmost position
- Remainder → emits `tab_rename_requested(index)` → opens an inline `QLineEdit` over the tab label

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
- Wires Ctrl+Z / Ctrl+Shift+Z shortcuts to the undo stack.
- Handles cross-list drag-drop by finding the source list and pushing `MoveItemBetweenListsCommand`.
- `_sync_data_model()` rebuilds `AppData` from widget state before saving.
- `closeEvent` calls `_sync_data_model()` then `storage.save()`.

**Public API** (called by undo commands):
`move_tab_to_front(from, to)`, `rename_tab(index, new_name)`, `transfer_item(from_list, from_item, to_list, to_item, text)`

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

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `PySide6` | 6.10+ | Qt GUI framework |
| `tomli_w` | 1.2+ | Write TOML files |
| `tomllib` | stdlib (3.11+) | Read TOML files |
