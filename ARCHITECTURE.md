# MyTodo — Architecture

## Overview

A desktop todo app built with Python 3 and PySide6 (Qt). Lists are displayed as tabs; each list contains plain-text items that can be edited, reordered by drag-and-drop, and promoted to the top with a double-click. All mutations are undoable with Ctrl+Z. State is persisted to a TOML file on disk.

## Running

```bash
python3 main.py
```

Data is saved automatically to `.mytodo.toml` in the project directory when the window closes.

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

## Documentation

| Topic | File |
|---|---|
| Entry point | [documentation/main.md](documentation/main.md) |
| Data model | [documentation/data.md](documentation/data.md) |
| Persistence (TOML) | [documentation/storage.md](documentation/storage.md) |
| Visual constants | [documentation/style.md](documentation/style.md) |
| Single item row | [documentation/item_widget.md](documentation/item_widget.md) |
| Per-list widget | [documentation/list_widget.md](documentation/list_widget.md) |
| Main window | [documentation/window.md](documentation/window.md) |
| Undo stack | [documentation/undo_commands.md](documentation/undo_commands.md) |
| Keyboard shortcuts | [documentation/keyboard_shortcuts.md](documentation/keyboard_shortcuts.md) |
| Dependencies | [documentation/dependencies.md](documentation/dependencies.md) |
