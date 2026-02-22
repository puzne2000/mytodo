"""Custom widget for a single todo item: a text box + a hot zone strip."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QTextEdit, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QPalette


HOT_ZONE_WIDTH = 16  # px wide strip on the left side of each item


class HotZone(QFrame):
    """Narrow clickable strip; double-click promotes the item to top."""
    double_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(HOT_ZONE_WIDTH)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Double-click to move to top")
        self.setStyleSheet(
            "QFrame { background: #b0c4de; border-radius: 3px; }"
            "QFrame:hover { background: #4682b4; }"
        )

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        event.accept()


class ItemTextEdit(QTextEdit):
    """Single-item text editor that emits editing_finished when focus leaves."""
    editing_finished = Signal(str)   # emits new text
    editing_started = Signal(str)    # emits old text (before edit begins)

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
            "QTextEdit:focus { background: #fffde7; border: 1px solid #aaa; border-radius: 2px; }"
        )

    def _adjust_height(self):
        doc_height = int(self.document().size().height())
        self.setFixedHeight(max(doc_height + 6, 28))

    def focusInEvent(self, event):
        self._original_text = self.toPlainText()
        self.editing_started.emit(self._original_text)
        super().focusInEvent(event)

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

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        self.hot_zone = HotZone(self)
        self.hot_zone.double_clicked.connect(self.promote_requested)

        self.text_edit = ItemTextEdit(text, self)
        self.text_edit.editing_finished.connect(
            lambda new: self.edit_committed.emit(self.text_edit._original_text, new)
        )

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
