# MyTodo — Build Status

## Current state
All features are on the `main` branch and functional.

## What has been built
- Tab-based lists with drag-and-drop reorder within a list
- In-place text editing per item, auto-resizing
- Hot zone strip on each item (left edge): double-click → promote to top of list; drag → drop on a tab to move item to that list (lands at position 0)
- Hot zone on each tab (left edge): double-click → promote list to leftmost tab
- Double-click tab name → inline rename editor (undo-able)
- Full undo stack (`QUndoStack`) for every operation
- Cmd+S to save at any time; auto-save on close
- Keyboard navigation: Enter starts editing; Escape finishes editing (or deselects if not editing); Cmd+Down/Up moves between items while editing; Up on first item deselects; Down when nothing selected selects first item; Left/Right when nothing selected navigates between lists
- Switching tabs clears item selection; focus explicitly given to `TodoListWidget` via `QTimer.singleShot(0)` to prevent Qt's focus restoration from re-entering edit mode
- Selection border ring drawn by `ItemWidget.paintEvent`; driven by `TodoListWidget._on_selection_changed` via `currentItemChanged` signal — note: `QListWidget::item:selected` border is invisible (covered by ItemWidget), so the ring must be drawn by the widget itself
- Tab flash animation on cross-list drop (fading blue overlay, `QVariantAnimation`)
- `style.py` — all visual constants (colours, dimensions, animation params) in one place
- Cmd+Backspace (item selected, not editing): deletes item; selects next item below, or previous if last, or focuses list if empty
- Delete item button: deletes selected item if one is selected; if no item selected and list is empty, deletes the list (undoable); does nothing if list has items but none selected

## Things not yet built
- **New item from keyboard** (e.g. Cmd+N or Enter at end of list)
