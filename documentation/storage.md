# `storage.py` — Persistence

Reads and writes `.mytodo.toml` in the project directory (same folder as `storage.py`) using:
- `tomllib` (Python 3.11+ stdlib) for reading
- `tomli_w` (third-party, pip) for writing

**File format:**
```toml
[[lists]]
name = "Work"
items = ["Write report", "Schedule meeting"]

[[lists]]
name = "Personal"
items = ["Buy groceries"]
```

`DEFAULT_PATH` is `Path(__file__).parent / ".mytodo.toml"` — the project directory.
`load(path) -> AppData` — returns an empty `AppData` if the file does not exist.
`save(app, path)` — overwrites the file with current state.
