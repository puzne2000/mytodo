"""Custom list widget with drag-and-drop, hot-zone promotion, and undo support."""

from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QAbstractItemView, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QMimeData, QByteArray
from PySide6.QtGui import QDrag

from item_widget import ItemWidget


_MIME_TYPE = "application/x-mytodo-item"
_TEXT_ROLE = Qt.ItemDataRole.UserRole


class TodoListWidget(QListWidget):
    """
    Displays todo items as custom ItemWidgets inside QListWidgetItems.
    Supports:
    - Internal drag-to-reorder
    - Cross-list drag via custom MIME data
    - Double-click hot zone to promote item to top
    """
    # Signals to the window for cross-list drops
    cross_list_drop_received = Signal(int, str)  # dest_index, text
    cross_list_drop_sent = Signal(int)            # src_index that was removed

    def __init__(self, items: list[str], undo_stack, parent=None):
        super().__init__(parent)
        self._undo_stack = undo_stack

        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSpacing(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "QListWidget { border: none; background: #f5f5f5; }"
            "QListWidget::item { background: white; border: 1px solid #ddd;"
            "  border-radius: 4px; margin: 1px; }"
            "QListWidget::item:selected { background: #e3f2fd; border-color: #90caf9; }"
        )

        for text in items:
            self._append_row(text)

    # ------------------------------------------------------------------ #
    # Public helpers (called by undo commands and window)                  #
    # ------------------------------------------------------------------ #

    def set_item_text(self, index: int, text: str) -> None:
        item = self.item(index)
        if item:
            item.setData(_TEXT_ROLE, text)
            w = self.itemWidget(item)
            if w:
                w.set_text(text)

    def move_item_to_top(self, index: int) -> None:
        if index == 0:
            return
        self._move_row(index, 0)

    def move_item_from_top(self, original_index: int) -> None:
        self._move_row(0, original_index)

    def reorder_item(self, from_index: int, to_index: int) -> None:
        self._move_row(from_index, to_index)

    def append_item(self, text: str) -> None:
        self._append_row(text)

    def remove_last_item(self) -> None:
        if self.count() > 0:
            self.takeItem(self.count() - 1)

    def remove_item(self, index: int) -> None:
        self.takeItem(index)

    def insert_item(self, index: int, text: str) -> None:
        item = QListWidgetItem()
        item.setData(_TEXT_ROLE, text)
        self.insertItem(index, item)
        w = self._make_widget(text, item)
        self.setItemWidget(item, w)
        self._sync_size(item, w)

    def all_texts(self) -> list[str]:
        return [self.item(i).data(_TEXT_ROLE) or "" for i in range(self.count())]

    # ------------------------------------------------------------------ #
    # Drag and drop overrides                                              #
    # ------------------------------------------------------------------ #

    def startDrag(self, supported_actions):
        index = self.currentRow()
        if index < 0:
            return
        text = self.item(index).data(_TEXT_ROLE) or ""

        mime = QMimeData()
        payload = f"{id(self)}|{index}|{text}"
        mime.setData(_MIME_TYPE, QByteArray(payload.encode()))

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(_MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(_MIME_TYPE):
            super().dropEvent(event)
            return

        payload = bytes(event.mimeData().data(_MIME_TYPE)).decode()
        source_id_str, from_index_str, text = payload.split("|", 2)
        from_index = int(from_index_str)
        source_id = int(source_id_str)

        dest_item = self.itemAt(event.position().toPoint())
        to_index = self.row(dest_item) if dest_item else self.count()

        if source_id == id(self):
            # Same-list reorder
            if from_index != to_index:
                from undo_commands import ReorderItemCommand
                self._undo_stack.push(ReorderItemCommand(self, from_index, to_index))
        else:
            # Cross-list drop: signal window to coordinate undo command
            self.cross_list_drop_received.emit(to_index, text)

        event.acceptProposedAction()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _append_row(self, text: str) -> QListWidgetItem:
        item = QListWidgetItem()
        item.setData(_TEXT_ROLE, text)
        self.addItem(item)
        w = self._make_widget(text, item)
        self.setItemWidget(item, w)
        self._sync_size(item, w)
        return item

    def _make_widget(self, text: str, item: QListWidgetItem) -> ItemWidget:
        w = ItemWidget(text, self)
        w.promote_requested.connect(lambda: self._on_promote(item))
        w.edit_committed.connect(lambda old, new: self._on_edit(item, old, new))
        w.text_edit.document().contentsChanged.connect(
            lambda: self._on_text_changed(item, w)
        )
        return w

    def _on_promote(self, item: QListWidgetItem) -> None:
        index = self.row(item)
        from undo_commands import MoveItemToTopCommand
        self._undo_stack.push(MoveItemToTopCommand(self, index))

    def _on_edit(self, item: QListWidgetItem, old_text: str, new_text: str) -> None:
        index = self.row(item)
        item.setData(_TEXT_ROLE, new_text)
        from undo_commands import EditItemCommand
        self._undo_stack.push(EditItemCommand(self, index, old_text, new_text))

    def _on_text_changed(self, item: QListWidgetItem, w: ItemWidget) -> None:
        """Keep UserRole in sync with live text so drag/drop picks up edits."""
        item.setData(_TEXT_ROLE, w.text())
        self._sync_size(item, w)

    def _move_row(self, from_index: int, to_index: int) -> None:
        """Physically move a row, preserving its text and widget."""
        item = self.item(from_index)
        text = item.data(_TEXT_ROLE) or ""
        self.takeItem(from_index)
        # Adjust target after removal
        actual_to = to_index if to_index <= from_index else to_index - 1
        new_item = QListWidgetItem()
        new_item.setData(_TEXT_ROLE, text)
        self.insertItem(actual_to, new_item)
        w = self._make_widget(text, new_item)
        self.setItemWidget(new_item, w)
        self._sync_size(new_item, w)

    def _sync_size(self, item: QListWidgetItem, w: ItemWidget) -> None:
        item.setSizeHint(w.sizeHint())
