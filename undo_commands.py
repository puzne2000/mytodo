"""QUndoCommand subclasses for all reversible operations."""

from PySide6.QtGui import QUndoCommand


class EditItemCommand(QUndoCommand):
    def __init__(self, list_widget, item_index: int, old_text: str, new_text: str):
        super().__init__(f"Edit item")
        self._list_widget = list_widget
        self._item_index = item_index
        self._old_text = old_text
        self._new_text = new_text

    def redo(self):
        self._list_widget.set_item_text(self._item_index, self._new_text)

    def undo(self):
        self._list_widget.set_item_text(self._item_index, self._old_text)


class MoveItemToTopCommand(QUndoCommand):
    def __init__(self, list_widget, item_index: int):
        super().__init__("Move item to top")
        self._list_widget = list_widget
        self._item_index = item_index

    def redo(self):
        self._list_widget.move_item_to_top(self._item_index)

    def undo(self):
        # Move the item (now at index 0) back to its original position
        self._list_widget.move_item_from_top(self._item_index)


class ReorderItemCommand(QUndoCommand):
    def __init__(self, list_widget, from_index: int, to_index: int):
        super().__init__("Reorder item")
        self._list_widget = list_widget
        self._from_index = from_index
        self._to_index = to_index

    def redo(self):
        self._list_widget.reorder_item(self._from_index, self._to_index)

    def undo(self):
        self._list_widget.reorder_item(self._to_index, self._from_index)


class MoveItemBetweenListsCommand(QUndoCommand):
    def __init__(self, window, from_list_index: int, from_item_index: int,
                 to_list_index: int, to_item_index: int, text: str):
        super().__init__("Move item between lists")
        self._window = window
        self._from_list = from_list_index
        self._from_item = from_item_index
        self._to_list = to_list_index
        self._to_item = to_item_index
        self._text = text

    def redo(self):
        self._window.transfer_item(
            self._from_list, self._from_item,
            self._to_list, self._to_item,
            self._text
        )

    def undo(self):
        self._window.transfer_item(
            self._to_list, self._to_item,
            self._from_list, self._from_item,
            self._text
        )


class MoveListToFrontCommand(QUndoCommand):
    def __init__(self, window, list_index: int):
        super().__init__("Move list to front")
        self._window = window
        self._list_index = list_index

    def redo(self):
        self._window.move_tab_to_front(self._list_index)

    def undo(self):
        self._window.move_tab_to_front(0, self._list_index)


class AddItemCommand(QUndoCommand):
    def __init__(self, list_widget, text: str = ""):
        super().__init__("Add item")
        self._list_widget = list_widget
        self._text = text

    def redo(self):
        self._list_widget.append_item(self._text)

    def undo(self):
        self._list_widget.remove_last_item()


class DeleteItemCommand(QUndoCommand):
    def __init__(self, list_widget, item_index: int, text: str):
        super().__init__("Delete item")
        self._list_widget = list_widget
        self._item_index = item_index
        self._text = text

    def redo(self):
        self._list_widget.remove_item(self._item_index)

    def undo(self):
        self._list_widget.insert_item(self._item_index, self._text)


class RenameTabCommand(QUndoCommand):
    def __init__(self, window, index: int, old_name: str, new_name: str):
        super().__init__("Rename list")
        self._window = window
        self._index = index
        self._old_name = old_name
        self._new_name = new_name

    def redo(self):
        self._window.rename_tab(self._index, self._new_name)

    def undo(self):
        self._window.rename_tab(self._index, self._old_name)
