# `window.py` — Main Window

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
- Wires Ctrl+Z / Ctrl+Shift+Z, Cmd+S, Cmd+=, and Cmd++ shortcuts to undo, save, new item, and new list.
- Handles cross-list drag-drop by finding the source list and pushing `MoveItemBetweenListsCommand`.
- `_save()` syncs widget state into `AppData` and writes to disk; called by both Cmd+S and `closeEvent`.
- `_on_tab_changed(index)` — clears item selection in the newly active list and posts `QTimer.singleShot(0, lw.setFocus)` to give focus to the `TodoListWidget` after Qt's own focus restoration runs (prevents Qt from restoring focus to an `ItemTextEdit` and silently entering edit mode).
- `_on_navigate_tab(delta)` — moves to the adjacent tab (clamped to valid range) in response to `navigate_tab_requested` from the active list widget.
- `_on_delete_item()` — if an item is selected, pushes `DeleteItemCommand`; if no item is selected and the list is empty, pushes `DeleteListCommand`; does nothing if the list has items but none is selected.

**Public API** (called by undo commands):
`move_tab_to_front(from, to)`, `rename_tab(index, new_name)`, `remove_tab(index)`, `insert_tab(index, name)`, `transfer_item(from_list, from_item, to_list, to_item, text)`
