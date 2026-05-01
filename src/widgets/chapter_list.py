from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor


ICON_PENDING = "○"
ICON_RUNNING = "⟳"
ICON_DONE    = "✓"
ICON_ERROR   = "✗"

_COLOR_PENDING = "#64748b"
_COLOR_RUNNING = "#a78bfa"
_COLOR_DONE    = "#22c55e"
_COLOR_ERROR   = "#ef4444"


class _ChapterItemData:
    """Small value object that holds the state for one chapter row."""
    __slots__ = ("index", "title", "icon", "color")

    def __init__(self, index: int, title: str) -> None:
        self.index = index
        self.title = title
        self.icon  = ICON_PENDING
        self.color = _COLOR_PENDING


class ChapterListPanel(QWidget):
    chapter_selected = pyqtSignal(int, str)   # chapter_index, title

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("chapter-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self._title_lbl = QLabel("Chapters")
        self._title_lbl.setObjectName("panel-title")
        layout.addWidget(self._title_lbl)

        self._list = QListWidget()
        self._list.setObjectName("chapter-list")
        self._list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self._list)

        # index -> _ChapterItemData
        self._data: dict[int, _ChapterItemData] = {}

    # ── Public API ────────────────────────────────────────────────────

    def load_chapters(self, chapters: list[tuple[int, str]]) -> None:
        self._list.clear()
        self._data.clear()
        for idx, title in chapters:
            d = _ChapterItemData(idx, title)
            self._data[idx] = d
            self._list.addItem(self._make_item(d))
        count = len(chapters)
        self._title_lbl.setText(f"Chapters ({count})")

    def clear(self) -> None:
        self._list.clear()
        self._data.clear()
        self._title_lbl.setText("Chapters")

    def set_running(self, chapter_idx: int) -> None:
        self._update(chapter_idx, ICON_RUNNING, _COLOR_RUNNING)

    def set_done(self, chapter_idx: int) -> None:
        self._update(chapter_idx, ICON_DONE, _COLOR_DONE)

    def set_error(self, chapter_idx: int) -> None:
        self._update(chapter_idx, ICON_ERROR, _COLOR_ERROR)

    # ── Internals ─────────────────────────────────────────────────────

    def _make_item(self, d: _ChapterItemData) -> QListWidgetItem:
        item = QListWidgetItem(_fmt(d.index, d.title, d.icon))
        item.setData(Qt.ItemDataRole.UserRole, d.index)
        item.setForeground(QColor(d.color))
        return item

    def _update(self, chapter_idx: int, icon: str, color: str) -> None:
        d = self._data.get(chapter_idx)
        if d is None:
            return
        d.icon  = icon
        d.color = color
        for row in range(self._list.count()):
            item = self._list.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole) == chapter_idx:
                item.setText(_fmt(d.index, d.title, d.icon))
                item.setForeground(QColor(color))
                break

    def _on_row_changed(self, row: int) -> None:
        if row < 0:
            return
        item = self._list.item(row)
        if item:
            idx = item.data(Qt.ItemDataRole.UserRole)
            d   = self._data.get(idx)
            if d:
                self.chapter_selected.emit(d.index, d.title)


def _fmt(index: int, title: str, icon: str) -> str:
    short = title[:36] + "…" if len(title) > 37 else title
    return f"{icon}  Ch. {index}: {short}"

