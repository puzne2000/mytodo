# `undo_commands.py` — Undo Stack

All operations are reversible via `QUndoCommand` subclasses pushed onto the shared `QUndoStack`. Each command stores enough state to fully redo and undo the operation.

| Command | Redo | Undo |
|---|---|---|
| `EditItemCommand` | set item text to new | set item text to old |
| `MoveItemToTopCommand` | move item to index 0 | move item back to original index |
| `ReorderItemCommand` | move from → to | move to → from |
| `MoveItemBetweenListsCommand` | remove from src, insert at dst | remove from dst, insert at src |
| `MoveListToFrontCommand` | move tab to index 0 | move tab back to original index |
| `RenameTabCommand` | set tab text to new name | set tab text to old name |
| `AddItemCommand` | append blank item | remove last item |
| `DeleteItemCommand` | remove item at index | re-insert item at index with saved text |
| `DeleteListCommand` | remove tab at index | re-insert empty tab at index with saved name |
