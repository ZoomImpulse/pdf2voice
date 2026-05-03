from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea,
    QSizePolicy, QPushButton, QTextEdit,
)
from PyQt6.QtCore import pyqtSignal, Qt


class PreviewPanel(QWidget):
    edit_saved = pyqtSignal(int, str)   # chapter_index, joined edited text

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

        self._edit_btn = QPushButton("✎  Edit")
        self._edit_btn.setObjectName("btn-edit-chapter")
        self._edit_btn.setVisible(False)
        self._edit_btn.clicked.connect(self._enter_edit_mode)
        hl.addWidget(self._edit_btn)

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

        # Internal state
        self._edit_allowed   = False
        self._in_edit_mode   = False
        self._current_index  = -1
        self._current_title  = ""
        self._current_chunks: list[str] = []
        self._current_subdivision = ""
        self._current_announcement = ""
        self._text_edit: QTextEdit | None = None
        self._char_lbl: QLabel | None = None

        self._show_placeholder_widget()

    # ── Public API ────────────────────────────────────────────────────

    def set_edit_allowed(self, allowed: bool) -> None:
        self._edit_allowed = allowed
        if not allowed:
            self._edit_btn.setVisible(False)
        elif self._current_index >= 0 and not self._in_edit_mode:
            self._edit_btn.setVisible(True)

    def clear(self) -> None:
        self._edit_btn.setVisible(False)
        self._in_edit_mode = False
        self._current_index = -1
        self._show_placeholder_widget()

    def show_placeholder(
        self, message: str = "Select a chapter to preview its TTS content."
    ) -> None:
        lbl = self._scroll.widget()
        if isinstance(lbl, QLabel) and lbl.objectName() == "preview-placeholder":
            lbl.setText(message)
        else:
            self._show_placeholder_widget(message)
        self._edit_btn.setVisible(False)
        self._in_edit_mode = False

    def show_chapter(
        self,
        index: int,
        title: str,
        chunks: list[str],
        subdivision_type: str,
        title_announcement: str,
    ) -> None:
        # Cache for edit mode
        self._current_index        = index
        self._current_title        = title
        self._current_chunks       = list(chunks)
        self._current_subdivision  = subdivision_type
        self._current_announcement = title_announcement
        self._in_edit_mode         = False

        self._render_read_only()

        if self._edit_allowed:
            self._edit_btn.setVisible(True)
            self._edit_btn.setText("✎  Edit")
            self._edit_btn.setEnabled(True)
        else:
            self._edit_btn.setVisible(False)

    # ── Private: read-only rendering ──────────────────────────────────

    def _render_read_only(self) -> None:
        index             = self._current_index
        title             = self._current_title
        chunks            = self._current_chunks
        subdivision_type  = self._current_subdivision
        title_announcement = self._current_announcement

        content = QWidget()
        content.setObjectName("preview-content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 20, 20, 32)
        cl.setSpacing(0)

        # ── Chapter title ─────────────────────────────────────────────
        label = f"{subdivision_type} {index}"
        full  = f"{label} – {title}" if title.strip() else label
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

    # ── Private: edit mode ────────────────────────────────────────────

    def _enter_edit_mode(self) -> None:
        self._in_edit_mode = True
        self._edit_btn.setVisible(False)

        content = QWidget()
        content.setObjectName("preview-content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(10)

        # Chapter title label
        label = f"{self._current_subdivision} {self._current_index}"
        full  = f"{label} – {self._current_title}" if self._current_title.strip() else label
        ch_title = QLabel(full)
        ch_title.setObjectName("preview-chapter-title")
        ch_title.setWordWrap(True)
        cl.addWidget(ch_title)

        hint = QLabel("Bearbeite den Text. Absätze (Leerzeile) werden beim Speichern neu in Chunks aufgeteilt.")
        hint.setObjectName("preview-meta")
        hint.setWordWrap(True)
        cl.addWidget(hint)

        # Text editor with chunks joined by double newline
        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("chapter-text-edit")
        self._text_edit.setPlainText("\n\n".join(self._current_chunks))
        self._text_edit.textChanged.connect(self._update_char_count)
        cl.addWidget(self._text_edit, stretch=1)

        self._char_lbl = QLabel("")
        self._char_lbl.setObjectName("preview-meta")
        cl.addWidget(self._char_lbl)
        self._update_char_count()

        # Save / Cancel buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setObjectName("btn-edit-cancel")
        cancel_btn.clicked.connect(self._cancel_edit)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("✓  Speichern & Re-chunk")
        save_btn.setObjectName("btn-edit-save")
        save_btn.clicked.connect(self._save_edit)
        btn_row.addWidget(save_btn)

        cl.addLayout(btn_row)

        self._scroll.setWidget(content)
        self._scroll.verticalScrollBar().setValue(0)

    def _update_char_count(self) -> None:
        if self._text_edit and self._char_lbl:
            n = len(self._text_edit.toPlainText())
            self._char_lbl.setText(f"{n:,} Zeichen")

    def _cancel_edit(self) -> None:
        self._in_edit_mode = False
        self._render_read_only()
        if self._edit_allowed:
            self._edit_btn.setVisible(True)

    def _save_edit(self) -> None:
        if self._text_edit is None:
            return
        text = self._text_edit.toPlainText().strip()
        self._in_edit_mode = False
        # Emit raw text; app.py handles re-chunking and data updates
        self.edit_saved.emit(self._current_index, text)

    # ── Internals ─────────────────────────────────────────────────────

    def _show_placeholder_widget(
        self, message: str = "Select a chapter to preview its TTS content."
    ) -> None:
        lbl = QLabel(message)
        lbl.setObjectName("preview-placeholder")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        self._scroll.setWidget(lbl)
