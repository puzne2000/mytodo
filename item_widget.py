"""Custom widget for a single todo item: a text box + a hot zone strip."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QTextEdit, QSizePolicy, QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QColor, QPalette

import style


class HotZone(QFrame):
    """Narrow clickable strip; double-click promotes the item to top,
    drag moves the item to another list."""
    double_clicked = Signal()
    drag_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start: QPoint | None = None
        self.setFixedWidth(style.ITEM_HOT_ZONE_WIDTH)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Double-click to move to top  |  Drag to another list")
        self.setStyleSheet(
            f"QFrame {{ background: {style.ITEM_HOT_ZONE_COLOR}; border-radius: 3px; }}"
            f"QFrame:hover {{ background: {style.ITEM_HOT_ZONE_HOVER_COLOR}; }}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (self._drag_start is not None
                and event.buttons() & Qt.MouseButton.LeftButton):
            dist = (event.position().toPoint() - self._drag_start).manhattanLength()
            if dist >= QApplication.startDragDistance():
                self._drag_start = None
                self.drag_requested.emit()
                return  # widget may be deleted by the time drag completes
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self._drag_start = None
        self.double_clicked.emit()
        event.accept()


class ItemTextEdit(QTextEdit):
    """Single-item text editor that emits editing_finished when focus leaves."""
    editing_finished = Signal(str)   # emits new text
    editing_started = Signal(str)    # emits old text (before edit begins)
    escape_pressed = Signal()
    navigate_requested = Signal(int) # +1 down, -1 up

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._original_text = text
        self.setAcceptRichText(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.document().contentsChanged.connect(self._adjust_height)
        self.setStyleSheet(
            "QTextEdit { border: none; background: transparent; padding: 2px; }"
            f"QTextEdit:focus {{ background: {style.ITEM_EDIT_FOCUS_BG};"
            f" border: 1px solid {style.ITEM_EDIT_FOCUS_BORDER}; border-radius: 2px; }}"
        )

    def _adjust_height(self):
        doc_height = int(self.document().size().height())
        self.setFixedHeight(max(doc_height + 6, 28))

    def focusInEvent(self, event):
        self._original_text = self.toPlainText()
        self.editing_started.emit(self._original_text)
        super().focusInEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
            event.accept()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:  # Cmd on macOS
            if event.key() == Qt.Key.Key_Down:
                self.navigate_requested.emit(1)
                event.accept()
                return
            if event.key() == Qt.Key.Key_Up:
                self.navigate_requested.emit(-1)
                event.accept()
                return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        new_text = self.toPlainText().strip()
        if new_text != self._original_text:
            self.editing_finished.emit(new_text)
            self._original_text = new_text
        super().focusOutEvent(event)

    def sizeHint(self) -> QSize:
        doc_height = int(self.document().size().height())
        return QSize(200, max(doc_height + 6, 28))


class ItemWidget(QWidget):
    """A single todo item row: [hot-zone | text-editor]."""
    promote_requested = Signal()
    edit_committed = Signal(str, str)   # old_text, new_text
    drag_requested = Signal()
    item_focused = Signal()             # emitted when the text editor gains focus
    editing_cancelled = Signal()        # emitted when Escape is pressed while editing
    navigate_requested = Signal(int)    # emitted with ±1 on Cmd+Down/Up

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        self.hot_zone = HotZone(self)
        self.hot_zone.double_clicked.connect(self.promote_requested)
        self.hot_zone.drag_requested.connect(self.drag_requested)

        self.text_edit = ItemTextEdit(text, self)
        self.text_edit.editing_finished.connect(
            lambda new: self.edit_committed.emit(self.text_edit._original_text, new)
        )
        self.text_edit.editing_started.connect(lambda _: self.item_focused.emit())
        self.text_edit.escape_pressed.connect(self.editing_cancelled)
        self.text_edit.navigate_requested.connect(self.navigate_requested)

        layout.addWidget(self.hot_zone)
        layout.addWidget(self.text_edit)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def text(self) -> str:
        return self.text_edit.toPlainText()

    def set_text(self, text: str) -> None:
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(text)
        self.text_edit._original_text = text
        self.text_edit.blockSignals(False)
