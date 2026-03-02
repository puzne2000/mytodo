# `list_widget.py` — Per-List Widget

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
