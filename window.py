"""Main application window: a QTabWidget wrapping TodoListWidgets."""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QPushButton, QHBoxLayout, QInputDialog, QMessageBox, QTabBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QUndoStack, QKeySequence, QShortcut

import storage
from data import AppData
from list_widget import TodoListWidget
from undo_commands import (
    MoveListToFrontCommand, MoveItemBetweenListsCommand,
    AddItemCommand, DeleteItemCommand
)


class HotTabBar(QTabBar):
    """Tab bar where double-clicking a tab's hot zone moves the list to front."""
    tab_promoted = Signal(int)

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.position().toPoint())
        if index >= 0:
            self.tab_promoted.emit(index)
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyTodo")
        self.resize(700, 500)

        self._app_data = storage.load()
        self._undo_stack = QUndoStack(self)

        # Undo / Redo shortcuts
        QShortcut(QKeySequence.StandardKey.Undo, self, self._undo_stack.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, self._undo_stack.redo)

        self._build_ui()
        self._load_data()

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_new_list = QPushButton("+ New list")
        btn_new_list.clicked.connect(self._on_new_list)
        btn_new_item = QPushButton("+ New item")
        btn_new_item.clicked.connect(self._on_new_item)
        btn_del_item = QPushButton("Delete item")
        btn_del_item.clicked.connect(self._on_delete_item)
        for btn in (btn_new_list, btn_new_item, btn_del_item):
            btn.setFixedHeight(28)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        root.addLayout(toolbar)

        # Tabs
        self._tabs = QTabWidget()
        hot_bar = HotTabBar()
        hot_bar.tab_promoted.connect(self._on_tab_promoted)
        self._tabs.setTabBar(hot_bar)
        self._tabs.setTabsClosable(False)
        self._tabs.setMovable(False)  # we handle reorder manually
        root.addWidget(self._tabs)

    def _load_data(self):
        if not self._app_data.lists:
            # Seed with a default list
            self._app_data.add_list("My list")

        for todo_list in self._app_data.lists:
            self._add_tab(todo_list.name, todo_list.items)

    # ------------------------------------------------------------------ #
    # Tab management                                                       #
    # ------------------------------------------------------------------ #

    def _add_tab(self, name: str, items: list[str]) -> "TodoListWidget":
        lw = TodoListWidget(items, self._undo_stack)
        lw.cross_list_drop_received.connect(
            lambda to_idx, text, lw=lw: self._on_cross_drop_received(lw, to_idx, text)
        )
        self._tabs.addTab(lw, name)
        return lw

    def _list_widget_at(self, tab_index: int) -> "TodoListWidget":
        return self._tabs.widget(tab_index)

    def _current_list_widget(self) -> "TodoListWidget | None":
        return self._tabs.currentWidget()

    # ------------------------------------------------------------------ #
    # Public API used by undo commands                                     #
    # ------------------------------------------------------------------ #

    def move_tab_to_front(self, from_index: int, to_index: int = 0) -> None:
        """Move tab at from_index to to_index (default 0 = front)."""
        if from_index == to_index:
            return
        widget = self._tabs.widget(from_index)
        label = self._tabs.tabText(from_index)
        self._tabs.removeTab(from_index)
        self._tabs.insertTab(to_index, widget, label)
        self._tabs.setCurrentIndex(to_index)

    def transfer_item(
        self,
        from_list: int, from_item: int,
        to_list: int, to_item: int,
        text: str
    ) -> None:
        src = self._list_widget_at(from_list)
        dst = self._list_widget_at(to_list)
        src.remove_item(from_item)
        dst.insert_item(to_item, text)

    # ------------------------------------------------------------------ #
    # Toolbar actions                                                      #
    # ------------------------------------------------------------------ #

    def _on_new_list(self):
        name, ok = QInputDialog.getText(self, "New list", "List name:")
        if ok and name.strip():
            self._app_data.add_list(name.strip())
            self._add_tab(name.strip(), [])
            self._tabs.setCurrentIndex(self._tabs.count() - 1)

    def _on_new_item(self):
        lw = self._current_list_widget()
        if lw is None:
            return
        cmd = AddItemCommand(lw, "")
        self._undo_stack.push(cmd)
        # Focus the new item's text editor
        lw.setCurrentRow(lw.count() - 1)
        item = lw.item(lw.count() - 1)
        w = lw.itemWidget(item)
        if w:
            w.text_edit.setFocus()

    def _on_delete_item(self):
        lw = self._current_list_widget()
        if lw is None:
            return
        index = lw.currentRow()
        if index < 0:
            return
        item = lw.item(index)
        text = item.data(Qt.ItemDataRole.UserRole) or ""
        self._undo_stack.push(DeleteItemCommand(lw, index, text))

    # ------------------------------------------------------------------ #
    # Signal handlers                                                      #
    # ------------------------------------------------------------------ #

    def _on_tab_promoted(self, index: int) -> None:
        if index == 0:
            return
        self._undo_stack.push(MoveListToFrontCommand(self, index))

    def _on_cross_drop_received(self, dest_lw: "TodoListWidget", to_index: int, text: str):
        """Handle a cross-list drag: find source list and create undo command."""
        to_list_index = self._tabs.indexOf(dest_lw)

        # Find the source list widget (whichever has the matching item missing or present)
        # We rely on the dragged item still being in the source at this moment
        src_lw = None
        src_item_index = -1
        for i in range(self._tabs.count()):
            lw = self._list_widget_at(i)
            if lw is dest_lw:
                continue
            for j in range(lw.count()):
                if lw.item(j).data(Qt.ItemDataRole.UserRole) == text:
                    src_lw = lw
                    src_item_index = j
                    break
            if src_lw:
                break

        if src_lw is None:
            # Fallback: just insert without undo
            dest_lw.insert_item(to_index, text)
            return

        from_list_index = self._tabs.indexOf(src_lw)
        cmd = MoveItemBetweenListsCommand(
            self, from_list_index, src_item_index,
            to_list_index, to_index, text
        )
        self._undo_stack.push(cmd)

    # ------------------------------------------------------------------ #
    # Save on close                                                        #
    # ------------------------------------------------------------------ #

    def closeEvent(self, event):
        self._sync_data_model()
        storage.save(self._app_data)
        event.accept()

    def _sync_data_model(self):
        """Push current widget state back into AppData before saving."""
        self._app_data.lists.clear()
        for i in range(self._tabs.count()):
            lw = self._list_widget_at(i)
            name = self._tabs.tabText(i)
            self._app_data.add_list(name)
            self._app_data.lists[-1].items = lw.all_texts()
