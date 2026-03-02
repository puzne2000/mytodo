# `data.py` — Data Model

Pure Python dataclasses; no Qt dependency. Used as the canonical source of truth when loading and saving.

```
AppData
└── lists: list[TodoList]
    ├── name: str
    └── items: list[str]
```

`AppData` methods: `add_list`, `move_list_to_front`, `move_item_to_top`, `move_item`.
These are used only during load/save; the live UI state is held in the Qt widgets themselves and synced back to `AppData` at close time.
