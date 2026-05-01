from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt


class PreviewPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("preview-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("side-panel-header")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 10, 14, 10)
        title_lbl = QLabel("Preview")
        title_lbl.setObjectName("side-panel-title")
        hl.addWidget(title_lbl)
        hl.addStretch()
        layout.addWidget(hdr)

        sep = QFrame()
        sep.setObjectName("panel-sep")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # ── Scroll area ───────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._scroll, stretch=1)

        # Default placeholder
        self._show_placeholder_widget()

    # ── Public API ────────────────────────────────────────────────────

    def clear(self) -> None:
        self._show_placeholder_widget()

    def show_placeholder(
        self, message: str = "Select a chapter to preview its TTS content."
    ) -> None:
        lbl = self._scroll.widget()
        if isinstance(lbl, QLabel) and lbl.objectName() == "preview-placeholder":
            lbl.setText(message)
        else:
            self._show_placeholder_widget(message)

    def show_chapter(
        self,
        index: int,
        title: str,
        chunks: list[str],
        subdivision_type: str,
        title_announcement: str,
    ) -> None:
        content = QWidget()
        content.setObjectName("preview-content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 20, 20, 32)
        cl.setSpacing(0)

        # ── Chapter title ─────────────────────────────────────────────
        label = f"{subdivision_type} {index}"
        full  = f"{label} \u2013 {title}" if title.strip() else label
        ch_title = QLabel(full)
        ch_title.setObjectName("preview-chapter-title")
        ch_title.setWordWrap(True)
        ch_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        cl.addWidget(ch_title)
        cl.addSpacing(6)

        # ── Meta row ──────────────────────────────────────────────────
        total_chars = sum(len(c) for c in chunks)
        chunk_word  = "chunk" if len(chunks) == 1 else "chunks"
        meta = QLabel(f"{len(chunks)} {chunk_word}   ·   {total_chars:,} characters")
        meta.setObjectName("preview-meta")
        cl.addWidget(meta)
        cl.addSpacing(20)

        # ── Announcement card ─────────────────────────────────────────
        ann = QFrame()
        ann.setObjectName("preview-announcement")
        al = QVBoxLayout(ann)
        al.setContentsMargins(14, 10, 14, 12)
        al.setSpacing(5)

        ann_hdr = QLabel("TITLE ANNOUNCEMENT")
        ann_hdr.setObjectName("preview-ann-header")
        al.addWidget(ann_hdr)

        ann_txt = QLabel(title_announcement)
        ann_txt.setObjectName("preview-ann-text")
        ann_txt.setWordWrap(True)
        ann_txt.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        al.addWidget(ann_txt)

        cl.addWidget(ann)
        cl.addSpacing(24)

        # ── Content section label ─────────────────────────────────────
        sec_hdr = QLabel(f"CONTENT   ·   {len(chunks)} {chunk_word.upper()}")
        sec_hdr.setObjectName("preview-section-header")
        cl.addWidget(sec_hdr)
        cl.addSpacing(10)

        # ── Chunk cards ───────────────────────────────────────────────
        for i, chunk in enumerate(chunks, start=1):
            card = QFrame()
            card.setObjectName("preview-chunk-card")
            ck = QVBoxLayout(card)
            ck.setContentsMargins(14, 12, 14, 14)
            ck.setSpacing(8)

            # Header row: numbered badge + char count
            hrow = QHBoxLayout()
            hrow.setSpacing(8)

            badge = QLabel(str(i))
            badge.setObjectName("chunk-badge")
            badge.setFixedSize(22, 22)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hrow.addWidget(badge)

            chars_lbl = QLabel(f"{len(chunk):,} chars")
            chars_lbl.setObjectName("chunk-chars")
            hrow.addWidget(chars_lbl)
            hrow.addStretch()
            ck.addLayout(hrow)

            # Body text
            body = QLabel(chunk)
            body.setObjectName("chunk-body")
            body.setWordWrap(True)
            body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            ck.addWidget(body)

            cl.addWidget(card)
            if i < len(chunks):
                cl.addSpacing(8)

        cl.addStretch()

        self._scroll.setWidget(content)
        self._scroll.verticalScrollBar().setValue(0)

    # ── Internals ─────────────────────────────────────────────────────

    def _show_placeholder_widget(
        self, message: str = "Select a chapter to preview its TTS content."
    ) -> None:
        lbl = QLabel(message)
        lbl.setObjectName("preview-placeholder")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        self._scroll.setWidget(lbl)
