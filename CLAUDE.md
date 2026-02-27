# MyTodo — Project Context

## Project
- **Location**: `/Users/guykindler/My Drive/python stuff/mytodo`
- **Run**: `python3 main.py`
- **What it is**: A desktop todo app built with Python 3 + PySide6 (Qt). Lists are organised as tabs; each list contains plain-text items. All mutations are undoable (Ctrl+Z). State persists to `~/.mytodo.toml`.
- **Full technical reference**: `ARCHITECTURE.md` — covers every file, the data model, widget hierarchy, signal wiring, and keyboard shortcuts.

## How the user works
- **Short, incremental requests** — one feature or fix at a time
- **Discuss before building** — for anything non-trivial, give a brief discussion of approach/complexity before writing code. Don't jump straight to code
- **Code quality matters** — readability first. Keep things clean, well-separated, don't over-engineer. `style.py` is the right pattern (separate file for stylistic decisions)
- **Commit after each feature** — always commit when asked. Use descriptive commit messages
- **Update ARCHITECTURE.md when asked** — don't do it unsolicited
- **No emojis, no fluff** — concise, direct communication
- **Ask before doing anything large** — for multi-file changes or architectural decisions, describe the plan first

## Key technical details
- **Python 3.14** is the active interpreter (`/opt/homebrew/opt/python@3.14/...`). PySide6 and tomli_w are installed for it.
- **Drag-and-drop**: uses custom MIME type `application/x-mytodo-item` with payload `"<widget_id>|<from_index>|<text>"`. Same-list drops are handled in `list_widget.py`; cross-list drops (via hot zone drag to tab bar) are handled in `window.py`.
- **Row moves**: Qt detaches widget bindings on `takeItem`, so `_move_row` always creates a fresh `QListWidgetItem` + `ItemWidget` at the target position.
- **Safe drag pattern**: after emitting `drag_requested` in `HotZone.mouseMoveEvent`, return immediately — the widget may be deleted before `QDrag.exec()` returns.
- **macOS Cmd key**: in raw `keyPressEvent`, Cmd is `Qt.KeyboardModifier.ControlModifier` (Qt maps ⌘ to Ctrl on macOS).
- **Signal chain for editing**: `ItemTextEdit` → signals → `ItemWidget` → signals → `TodoListWidget` handles all the logic. Don't reach across layers.

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
HANDOFF.md         # current build status and recent history
```
