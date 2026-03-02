# `item_widget.py` — Single Item Row

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
