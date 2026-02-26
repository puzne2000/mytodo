# Agent Handoff — MyTodo App

## Project location
`/Users/guykindler/My Drive/python stuff/mytodo`

## What this app is
A desktop todo app built with Python 3 + PySide6 (Qt). Lists are organised as tabs; each list contains plain-text items. All mutations are undoable (Ctrl+Z). State persists to `~/.mytodo.toml`. Run with `python3 main.py`.

## Current state (as of handoff)
All features are on the `main` branch. The app is functional and tested by the user. See `ARCHITECTURE.md` in the project root for a full description of every file, the data model, widget hierarchy, signal wiring, and keyboard shortcuts.

### What has been built so far
- Tab-based lists with drag-and-drop reorder within a list
- In-place text editing per item, auto-resizing
- Hot zone strip on each item (left edge): double-click → promote to top of list; drag → drop on a tab to move item to that list (lands at position 0)
- Hot zone on each tab (left edge): double-click → promote list to leftmost tab
- Double-click tab name → inline rename editor (undo-able)
- Full undo stack (`QUndoStack`) for every operation
- Cmd+S to save at any time; auto-save on close
- Keyboard navigation: Enter starts editing; Escape finishes editing (or deselects item if not editing); Cmd+Down/Up moves between items while editing; Up on first item deselects; Down when nothing selected selects first item; Left/Right when nothing selected navigates between lists
- Switching tabs always clears item selection in the new list
- Selection border ring drawn by `ItemWidget.paintEvent` (uses `ITEM_SELECTED_BORDER` / `ITEM_SELECTED_BORDER_WIDTH` from `style.py`); driven by `TodoListWidget._on_selection_changed` via `currentItemChanged` signal — note: `QListWidget::item:selected` border is invisible (covered by ItemWidget), so the ring must be drawn by the widget itself
- List selection synced with which text editor has keyboard focus (Delete always acts on the item being edited)
- Tab flash animation on cross-list drop (fading blue overlay, `QVariantAnimation`)
- `style.py` — all visual constants (colours, dimensions, animation params) in one place

## How the user works
- **Short, incremental requests** — they ask for one feature or fix at a time
- **Discuss before building** — for anything non-trivial they want a brief discussion of approach/complexity before implementation. Don't jump straight to code
- **Code quality matters** — they care about readability. Keep things clean, well-separated, and don't over-engineer. They called out `style.py` as the right pattern (separate file for stylistic decisions)
- **Commit after each feature** — always commit when asked. Use descriptive commit messages
- **Update ARCHITECTURE.md when asked** — they periodically ask for it to be updated; don't do it unsolicited
- **No emojis, no fluff** — concise, direct communication
- **Ask before doing anything large** — for multi-file changes or architectural decisions, describe the plan first

## Key technical details to know
- **Python 3.14** is the active interpreter (`/opt/homebrew/opt/python@3.14/...`). PySide6 and tomli_w are installed for it.
- **Drag-and-drop**: uses custom MIME type `application/x-mytodo-item` with payload `"<widget_id>|<from_index>|<text>"`. Same-list drops are handled in `list_widget.py`; cross-list drops (via hot zone drag to tab bar) are handled in `window.py`.
- **Row moves**: Qt detaches widget bindings on `takeItem`, so `_move_row` always creates a fresh `QListWidgetItem` + `ItemWidget` at the target position.
- **Safe drag pattern**: after emitting `drag_requested` in `HotZone.mouseMoveEvent`, return immediately — the widget may be deleted before `QDrag.exec()` returns.
- **macOS Cmd key**: in raw `keyPressEvent`, Cmd is `Qt.KeyboardModifier.ControlModifier` (Qt maps ⌘ to Ctrl on macOS).
- **Signal chain for editing**: `ItemTextEdit` → signals → `ItemWidget` → signals → `TodoListWidget` handles all the logic. Don't reach across layers.

## Things discussed but not yet built
- **Deleting items with keyboard** (the user was building toward this; Delete key while an item is focused)
- **"New item" from keyboard** (e.g. Cmd+N or just pressing Enter at the end of a list)
- Scrolling behaviour for long lists was confirmed to work out of the box (QListWidget handles it automatically)

## Files
```
main.py            # entry point
window.py          # MainWindow, HotTabBar (tab rename, tab flash, cross-list drop)
list_widget.py     # TodoListWidget (items, drag-drop, keyboard nav)
item_widget.py     # ItemWidget, HotZone, ItemTextEdit
undo_commands.py   # all QUndoCommand subclasses
data.py            # AppData / TodoList dataclasses (no Qt)
storage.py         # TOML load/save → ~/.mytodo.toml
style.py           # all visual constants — edit here to change appearance
ARCHITECTURE.md    # full technical reference (keep this updated)
HANDOFF.md         # this file
```
