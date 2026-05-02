from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea,
)
from PyQt6.QtCore import pyqtSignal, Qt


_ACCENT_IDLE    = "#1e1e2e"
_ACCENT_RUNNING = "#7c3aed"
_ACCENT_DONE    = "#16a34a"
_ACCENT_ERROR   = "#dc2626"

_DOT_OBJECT = {
    "pending": "card-dot-pending",
    "running": "card-dot-running",
    "done":    "card-dot-done",
    "error":   "card-dot-error",
}


class _ChapterCard(QFrame):
    clicked_sig = pyqtSignal(int, str)

    def __init__(self, index: int, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._index = index
        self._title = title
        self._is_selected = False

        self.setObjectName("chapter-card")
        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 14, 0)
        root.setSpacing(10)

        # 3-px left accent bar
        self._accent = QFrame()
        self._accent.setFixedWidth(3)
        self._accent.setStyleSheet(f"background:{_ACCENT_IDLE};")
        root.addWidget(self._accent)

        # Status dot (coloured Unicode circle)
        self._dot = QLabel("●")
        self._dot.setObjectName(_DOT_OBJECT["pending"])
        self._dot.setFixedWidth(14)
        self._dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._dot)

        # Chapter number badge
        self._num_lbl = QLabel(f"{index:02d}")
        self._num_lbl.setObjectName("card-num")
        self._num_lbl.setFixedWidth(26)
        self._num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._num_lbl)

        # Thin vertical separator
        vsep = QFrame()
        vsep.setFixedWidth(1)
        vsep.setFixedHeight(24)
        vsep.setStyleSheet("background:#1e1e2e;")
        root.addWidget(vsep)

        # Title
        display = title or f"Chapter {index}"
        short = (display[:42] + "…") if len(display) > 43 else display
        self._title_lbl = QLabel(short)
        self._title_lbl.setObjectName("card-title")
        root.addWidget(self._title_lbl, stretch=1)

    # ── Events ────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        self.clicked_sig.emit(self._index, self._title)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self._is_selected:
            self.setStyleSheet("QFrame#chapter-card { background: #17171f; }")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._is_selected:
            self.setStyleSheet("")
        super().leaveEvent(event)

    # ── Public API ────────────────────────────────────────────────────

    def set_selected(self, on: bool) -> None:
        self._is_selected = on
        if on:
            self.setStyleSheet("QFrame#chapter-card { background: #160f2e; }")
            self._title_lbl.setStyleSheet("color: #e2e8f0;")
            self._num_lbl.setStyleSheet("color: #a78bfa;")
        else:
            self.setStyleSheet("")
            self._title_lbl.setStyleSheet("")
            self._num_lbl.setStyleSheet("")

    def set_state_running(self) -> None:
        self._apply_state(_ACCENT_RUNNING, "running")

    def set_state_done(self) -> None:
        self._apply_state(_ACCENT_DONE, "done")

    def set_state_error(self) -> None:
        self._apply_state(_ACCENT_ERROR, "error")

    # ── Internals ─────────────────────────────────────────────────────

    def _apply_state(self, accent: str, dot_key: str) -> None:
        self._accent.setStyleSheet(f"background:{accent};")
        self._dot.setObjectName(_DOT_OBJECT[dot_key])
        self._dot.style().unpolish(self._dot)
        self._dot.style().polish(self._dot)


class ChapterListPanel(QWidget):
    chapter_selected = pyqtSignal(int, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("chapter-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("side-panel-header")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 10, 14, 10)
        self._title_lbl = QLabel("Chapters")
        self._title_lbl.setObjectName("side-panel-title")
        hl.addWidget(self._title_lbl)
        hl.addStretch()
        layout.addWidget(hdr)

        sep = QFrame()
        sep.setObjectName("panel-sep")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # ── Scroll area ───────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._inner = QWidget()
        self._inner.setObjectName("panel-scroll-content")
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setContentsMargins(0, 4, 0, 8)
        self._inner_layout.setSpacing(1)
        self._inner_layout.addStretch()
        scroll.setWidget(self._inner)
        layout.addWidget(scroll, stretch=1)

        self._cards: dict[int, _ChapterCard] = {}
        self._selected: int | None = None

    # ── Public API ────────────────────────────────────────────────────

    def load_chapters(self, chapters: list[tuple[int, str]]) -> None:
        """Replace all chapters with the given list (full reload)."""
        while self._inner_layout.count() > 1:
            item = self._inner_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        self._selected = None

        for idx, title in chapters:
            card = _ChapterCard(idx, title)
            card.clicked_sig.connect(self._on_card_clicked)
            self._cards[idx] = card
            self._inner_layout.insertWidget(self._inner_layout.count() - 1, card)

        n = len(chapters)
        self._title_lbl.setText(f"Chapters  ·  {n}" if n else "Chapters")

    def add_chapters(self, chapters: list[tuple[int, str]]) -> None:
        """Add chapters progressively (for streaming during structuring)."""
        for idx, title in chapters:
            if idx not in self._cards:
                card = _ChapterCard(idx, title)
                card.clicked_sig.connect(self._on_card_clicked)
                self._cards[idx] = card
                self._inner_layout.insertWidget(self._inner_layout.count() - 1, card)

        n = len(self._cards)
        self._title_lbl.setText(f"Chapters  ·  {n}" if n else "Chapters")

    def clear(self) -> None:
        self.load_chapters([])
        self._title_lbl.setText("Chapters")

    def set_running(self, chapter_idx: int) -> None:
        if card := self._cards.get(chapter_idx):
            card.set_state_running()

    def set_done(self, chapter_idx: int) -> None:
        if card := self._cards.get(chapter_idx):
            card.set_state_done()

    def set_error(self, chapter_idx: int) -> None:
        if card := self._cards.get(chapter_idx):
            card.set_state_error()

    # ── Internals ─────────────────────────────────────────────────────

    def _on_card_clicked(self, idx: int, title: str) -> None:
        if self._selected is not None:
            if prev := self._cards.get(self._selected):
                prev.set_selected(False)
        self._selected = idx
        if card := self._cards.get(idx):
            card.set_selected(True)
        self.chapter_selected.emit(idx, title)

