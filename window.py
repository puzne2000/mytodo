"""Main application window: a QTabWidget wrapping TodoListWidgets."""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QPushButton, QHBoxLayout, QInputDialog, QMessageBox, QTabBar, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QVariantAnimation, QAbstractAnimation
from PySide6.QtGui import QUndoStack, QKeySequence, QShortcut, QPainter, QColor

import storage
import style
from data import AppData
from list_widget import TodoListWidget
from undo_commands import (
    MoveListToFrontCommand, MoveItemBetweenListsCommand,
    AddItemCommand, DeleteItemCommand, RenameTabCommand
)


_ITEM_MIME = "application/x-mytodo-item"


class HotTabBar(QTabBar):
    """Tab bar with two double-click zones per tab:
    - Left N px (hot zone): double-click promotes the list to front
    - Remainder (name area): double-click opens inline rename editor
    Also accepts item drops: dropping an item on a tab moves it to that list
    and briefly flashes the tab to confirm.
    """
    tab_promoted = Signal(int)
    tab_rename_requested = Signal(int)
    item_dropped_on_tab = Signal(int, str)  # tab_index, mime payload

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._flash_colors: dict[int, QColor] = {}
        self._flash_anims: dict[int, QVariantAnimation] = {}

    # ── Double-click zones ────────────────────────────────────────────────────

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.position().toPoint())
        if index >= 0:
            x_in_tab = event.position().toPoint().x() - self.tabRect(index).left()
            if x_in_tab <= style.TAB_HOT_ZONE_WIDTH:
                self.tab_promoted.emit(index)
            else:
                self.tab_rename_requested.emit(index)
        event.accept()

    # ── Drag-and-drop ─────────────────────────────────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_ITEM_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(_ITEM_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(_ITEM_MIME):
            event.ignore()
            return
        tab_index = self.tabAt(event.position().toPoint())
        if tab_index < 0:
            event.ignore()
            return
        payload = bytes(event.mimeData().data(_ITEM_MIME)).decode()
        self.item_dropped_on_tab.emit(tab_index, payload)
        event.acceptProposedAction()

    # ── Flash animation ───────────────────────────────────────────────────────

    def flash_tab(self, index: int) -> None:
        """Briefly highlight a tab with a fading colour overlay."""
        # Stop any in-progress animation for this tab
        if index in self._flash_anims:
            self._flash_anims[index].stop()

        anim = QVariantAnimation(self)
        anim.setStartValue(style.FLASH_COLOR)
        anim.setEndValue(QColor(style.FLASH_COLOR.red(),
                                style.FLASH_COLOR.green(),
                                style.FLASH_COLOR.blue(), 0))
        anim.setDuration(style.FLASH_DURATION_MS)
        anim.setEasingCurve(style.FLASH_EASING)
        anim.valueChanged.connect(lambda color, i=index: self._update_flash(i, color))
        anim.finished.connect(lambda i=index: self._clear_flash(i))
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        self._flash_colors[index] = style.FLASH_COLOR
        self._flash_anims[index] = anim

    def _update_flash(self, index: int, color: QColor) -> None:
        self._flash_colors[index] = color
        self.update()

    def _clear_flash(self, index: int) -> None:
        self._flash_colors.pop(index, None)
        self._flash_anims.pop(index, None)
        self.update()

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._flash_colors:
            return
        painter = QPainter(self)
        for index, color in self._flash_colors.items():
            painter.fillRect(self.tabRect(index), color)
        painter.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyTodo")
        self.resize(700, 500)

        self._app_data = storage.load()
        self._undo_stack = QUndoStack(self)

        # Shortcuts
        QShortcut(QKeySequence.StandardKey.Undo, self, self._undo_stack.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, self._undo_stack.redo)
        QShortcut(QKeySequence.StandardKey.Save, self, self._save)

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
        hot_bar.tab_rename_requested.connect(self._on_tab_rename_requested)
        hot_bar.item_dropped_on_tab.connect(self._on_item_dropped_on_tab)
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
        lw.navigate_tab_requested.connect(self._on_navigate_tab)
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

    def rename_tab(self, index: int, new_name: str) -> None:
        self._tabs.setTabText(index, new_name)

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

    def _on_navigate_tab(self, delta: int) -> None:
        new_index = max(0, min(self._tabs.currentIndex() + delta, self._tabs.count() - 1))
        self._tabs.setCurrentIndex(new_index)

    def _on_tab_promoted(self, index: int) -> None:
        if index == 0:
            return
        self._undo_stack.push(MoveListToFrontCommand(self, index))

    def _on_tab_rename_requested(self, index: int) -> None:
        old_name = self._tabs.tabText(index)
        tab_rect = self._tabs.tabBar().tabRect(index)

        editor = QLineEdit(old_name, self._tabs.tabBar())
        editor.setGeometry(tab_rect)
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        editor.setStyleSheet(
            f"QLineEdit {{ background: white; border: 1px solid {style.TAB_RENAME_BORDER};"
            "  border-radius: 2px; padding: 0 2px; }"
        )
        editor.selectAll()
        editor.show()
        editor.setFocus()

        def _commit():
            new_name = editor.text().strip()
            editor.deleteLater()
            if new_name and new_name != old_name:
                self._undo_stack.push(RenameTabCommand(self, index, old_name, new_name))

        editor.returnPressed.connect(_commit)
        editor.editingFinished.connect(_commit)

    def _on_item_dropped_on_tab(self, tab_index: int, payload: str) -> None:
        source_id_str, from_index_str, text = payload.split("|", 2)
        source_id = int(source_id_str)
        from_index = int(from_index_str)

        src_lw = None
        from_list_index = -1
        for i in range(self._tabs.count()):
            lw = self._list_widget_at(i)
            if id(lw) == source_id:
                src_lw = lw
                from_list_index = i
                break

        if src_lw is None or from_list_index == tab_index:
            return

        self._undo_stack.push(MoveItemBetweenListsCommand(
            self, from_list_index, from_index,
            tab_index, 0, text
        ))
        self._tabs.tabBar().flash_tab(tab_index)

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

    def _save(self):
        self._sync_data_model()
        storage.save(self._app_data)

    def closeEvent(self, event):
        self._save()
        event.accept()

    def _sync_data_model(self):
        """Push current widget state back into AppData before saving."""
        self._app_data.lists.clear()
        for i in range(self._tabs.count()):
            lw = self._list_widget_at(i)
            name = self._tabs.tabText(i)
            self._app_data.add_list(name)
            self._app_data.lists[-1].items = lw.all_texts()
