"""pdf2voice — Metadata card: shows book metadata after structuring."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class MetadataCard(QFrame):
    """Card showing detected book metadata with an option to reanalyze."""

    reanalyze_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("info-card")
        self.setVisible(False)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        # ── Header row ────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        title_lbl = QLabel("BOOK METADATA")
        title_lbl.setObjectName("info-card-title")
        hdr.addWidget(title_lbl)
        hdr.addStretch()

        self._reanalyze_btn = QPushButton("🔄  Reanalyze")
        self._reanalyze_btn.setObjectName("btn-reanalyze")
        self._reanalyze_btn.setFixedHeight(26)
        self._reanalyze_btn.setEnabled(False)
        self._reanalyze_btn.clicked.connect(self.reanalyze_requested.emit)
        hdr.addWidget(self._reanalyze_btn)

        outer.addLayout(hdr)

        # ── Title row (full width) ────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(6)

        k = QLabel("Title:")
        k.setObjectName("settings-key")
        k.setFixedWidth(76)
        self._title_val = QLabel("—")
        self._title_val.setObjectName("metadata-val")
        self._title_val.setWordWrap(True)
        title_row.addWidget(k)
        title_row.addWidget(self._title_val, stretch=1)
        outer.addLayout(title_row)

        # ── Details row ───────────────────────────────────────────────
        details = QHBoxLayout()
        details.setSpacing(24)
        self._genre_val    = self._kv("Genre",       details)
        self._lang_val     = self._kv("Language",    details)
        self._subdiv_val   = self._kv("Subdivision", details)
        self._chapters_val = self._kv("Chapters",    details)
        details.addStretch()
        outer.addLayout(details)

    def _kv(self, key: str, row: QHBoxLayout) -> QLabel:
        inner = QHBoxLayout()
        inner.setSpacing(4)
        k = QLabel(key + ":")
        k.setObjectName("settings-key")
        v = QLabel("—")
        v.setObjectName("metadata-val")
        inner.addWidget(k)
        inner.addWidget(v)
        row.addLayout(inner)
        return v

    # ── Public API ────────────────────────────────────────────────────

    def populate(self, book) -> None:
        self._title_val.setText(book.title or "—")
        self._genre_val.setText(book.genre or "—")
        self._lang_val.setText(book.language or "—")
        self._subdiv_val.setText(book.subdivision_type or "—")
        self._chapters_val.setText(str(len(book.chapters)))

        has_sample = bool(getattr(book, "metadata_sample", ""))
        self._reanalyze_btn.setEnabled(has_sample)
        self._reanalyze_btn.setToolTip(
            "" if has_sample
            else "Reanalysis not available for resumed sessions"
        )
        self.setVisible(True)

    def set_busy(self, busy: bool) -> None:
        self._reanalyze_btn.setEnabled(not busy)
        self._reanalyze_btn.setText("⏳  Analyzing…" if busy else "🔄  Reanalyze")

    def reset(self) -> None:
        self.setVisible(False)
