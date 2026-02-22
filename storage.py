"""Load and save app data as a TOML file."""

import tomllib
import tomli_w
from pathlib import Path
from data import AppData, TodoList

DEFAULT_PATH = Path.home() / ".mytodo.toml"


def load(path: Path = DEFAULT_PATH) -> AppData:
    if not path.exists():
        return AppData()
    with path.open("rb") as f:
        raw = tomllib.load(f)
    app = AppData()
    for lst_data in raw.get("lists", []):
        app.lists.append(TodoList(
            name=lst_data.get("name", ""),
            items=lst_data.get("items", []),
        ))
    return app


def save(app: AppData, path: Path = DEFAULT_PATH) -> None:
    raw = {
        "lists": [
            {"name": lst.name, "items": lst.items}
            for lst in app.lists
        ]
    }
    with path.open("wb") as f:
        tomli_w.dump(raw, f)
