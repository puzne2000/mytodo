# MyTodo

A keyboard-driven desktop todo app with tab-based lists, in-place editing, and full undo.

---

## Screenshot

<!-- Add a screenshot here -->

---

## Features

- Tab-based lists — one tab per list, reorderable
- In-place text editing with auto-resize
- Drag to reorder items within a list
- Drag to move items between lists (via the blue hot zone)
- Double-click the hot zone to promote an item to the top of its list
- Double-click the left edge of a tab to promote that list to the first position
- Full undo/redo (Cmd+Z / Cmd+Shift+Z)
- Persistent storage (`~/.mytodo.toml`)

---

## Requirements

- Python 3.11+
- PySide6
- tomli_w

---

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install PySide6 tomli_w
python3 main.py
```

---

## Keyboard shortcuts

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
| Down | no item selected | Select first item |
| Cmd+Backspace | item selected, not editing | Delete selected item |
| Left | no item selected | Navigate to previous list |
| Right | no item selected | Navigate to next list |

---

## Data

State is saved automatically to `~/.mytodo.toml` when the window closes, and can be saved manually with Cmd+S. The file is plain text and human-editable:

```toml
[[lists]]
name = "Work"
items = ["Write report", "Schedule meeting"]

[[lists]]
name = "Personal"
items = ["Buy groceries"]
```

---

<details>
<summary>Development</summary>

See `ARCHITECTURE.md` for file map, widget hierarchy, signal wiring, and design decisions.

</details>
