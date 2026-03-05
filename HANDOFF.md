# MyTodo — Build Status

## Current state
Active development is on the `dev` branch (`mytodo-dev` folder). Production is on `main` (`mytodo` folder), managed via git worktree. All features below are on `dev`.

## What has been built
- Tab-based lists with drag-and-drop reorder within a list
- In-place text editing per item, auto-resizing
- Hot zone strip on each item (left edge): double-click → promote to top of list; drag → drop on a tab to move item to that list (lands at position 0)
- Hot zone on each tab (left edge): double-click → promote list to leftmost tab
- Double-click tab name → inline rename editor (undo-able)
- Full undo stack (`QUndoStack`) for every operation
- Cmd+S to save at any time; auto-save on close
- Keyboard navigation: Enter starts editing; Escape finishes editing (or deselects + returns focus to list if not editing); Cmd+Down/Up moves between items while editing; Up on first item deselects; Down when nothing selected selects first item; Left/Right when nothing selected navigates between lists
- Switching tabs clears item selection; focus explicitly given to `TodoListWidget` via `QTimer.singleShot(0)` to prevent Qt's focus restoration from re-entering edit mode
- Selection border ring drawn by `ItemWidget.paintEvent`; driven by `TodoListWidget._on_selection_changed` via `currentItemChanged` signal
- Tab flash animation on cross-list drop (fading blue overlay, `QVariantAnimation`)
- `style.py` — all visual constants in one place; `WINDOW_BG` is orange-grey in `-dev` folder, neutral grey otherwise (detected via `pathlib.Path(__file__).parent.name`)
- Cmd+Backspace (item selected, not editing): deletes item
- Cmd+Backspace (editing, item has text): select-all + cursor delete — uses QTextEdit's own undo stack, so Cmd+Z restores text natively while still in edit mode
- Cmd+Backspace (editing, item empty): deletes the item via undo stack
- Delete item button: deletes selected item; if no item selected and list is empty, deletes the list; does nothing otherwise
- Cmd+= → new item; Cmd++ → new list
- ARCHITECTURE.md restructured: slim index only; detail split into `documentation/` folder (one file per module/topic)

## Things not yet built
- **Item IDs** — stable identifiers for items so they can be referenced externally
- **Vertical spacing bug** — items take too much vertical space; needs investigation
- **Temporary item hosting** — ability to park items in another list temporarily
- **Multi-list view** — view items from several lists at once
- **Central keyboard shortcut file** — consolidate all shortcuts into one place (currently spread across `window.py`, `list_widget.py`, `item_widget.py`)
- **Vim-inspired keyboard commands** — modal navigation/editing
- **Quick search** — search across items and lists
