"""pdf2voice — Chapter section: expandable chapter cards with inline preview."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


_ACCENT: dict[str, str] = {
    "pending": "#1e1e2e",
    "running": "#7c3aed",
    "done":    "#16a34a",
    "error":   "#dc2626",
}
_DOT_OBJ: dict[str, str] = {
    "pending": "card-dot-pending",
    "running": "card-dot-running",
    "done":    "card-dot-done",
    "error":   "card-dot-error",
}


class _ExpandableChapterCard(QFrame):
    """Chapter row that expands to show preview content inline."""

    clicked_sig   = pyqtSignal(int, str)
    regen_clicked = pyqtSignal(int)
    edit_saved    = pyqtSignal(int, str, str)   # index, new_title, new_text
    delete_clicked = pyqtSignal(int)

    def __init__(self, index: int, title: str, parent=None) -> None:
        super().__init__(parent)
        self._index      = index
        self._title      = title
        self._expanded   = False
        self._edit_allowed  = False
        self._in_edit_mode  = False
        self._chunks: list[str] = []
        self._subdivision   = ""
        self._announcement  = ""
        self._text_edit: QTextEdit | None = None
        self._title_edit: QLineEdit | None = None
        self._char_lbl:  QLabel | None = None

        self.setObjectName("exp-chapter-card")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header row ────────────────────────────────────────────────
        self._hdr = QFrame()
        self._hdr.setObjectName("exp-card-header")
        self._hdr.setCursor(Qt.CursorShape.PointingHandCursor)
        hl = QHBoxLayout(self._hdr)
        hl.setContentsMargins(14, 10, 14, 10)
        hl.setSpacing(10)

        self._expand_icon = QLabel("▸")
        self._expand_icon.setObjectName("exp-icon")
        self._expand_icon.setFixedWidth(14)
        hl.addWidget(self._expand_icon)

        self._dot = QFrame()
        self._dot.setObjectName(_DOT_OBJ["pending"])
        self._dot.setFixedSize(8, 8)
        hl.addWidget(self._dot)

        num_lbl = QLabel(f"{index:02d}")
        num_lbl.setObjectName("card-num")
        num_lbl.setFixedWidth(26)
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(num_lbl)

        vsep = QFrame()
        vsep.setFixedWidth(1)
        vsep.setFixedHeight(20)
        vsep.setStyleSheet("background:#1e1e2e;")
        hl.addWidget(vsep)

        display = title or f"Chapter {index}"
        short   = (display[:52] + "…") if len(display) > 53 else display
        self._title_lbl = QLabel(short)
        self._title_lbl.setObjectName("card-title")
        hl.addWidget(self._title_lbl, stretch=1)

        self._regen_btn = QPushButton("⟳")
        self._regen_btn.setObjectName("btn-regen")
        self._regen_btn.setFixedSize(26, 26)
        self._regen_btn.setToolTip("Regenerate this chapter")
        self._regen_btn.setVisible(False)
        self._regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._regen_btn.clicked.connect(lambda: self.regen_clicked.emit(self._index))
        hl.addWidget(self._regen_btn)

        root.addWidget(self._hdr)

        # ── Inner separator (only visible when expanded) ──────────────
        self._inner_sep = QFrame()
        self._inner_sep.setObjectName("card-sep")
        self._inner_sep.setFixedHeight(1)
        self._inner_sep.setVisible(False)
        root.addWidget(self._inner_sep)

        # ── Expandable content ────────────────────────────────────────
        self._content = QWidget()
        self._content.setObjectName("exp-card-content")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(14, 14, 14, 14)
        self._content_layout.setSpacing(10)
        self._content.setVisible(False)
        root.addWidget(self._content)

        # ── Bottom separator (always visible) ────────────────────────
        bot_sep = QFrame()
        bot_sep.setObjectName("card-sep")
        bot_sep.setFixedHeight(1)
        root.addWidget(bot_sep)

        # Wire header click
        self._hdr.mousePressEvent = self._on_header_click  # type: ignore[method-assign]

    # ── Events ────────────────────────────────────────────────────────

    def _on_header_click(self, event) -> None:
        if self._expanded:
            self._collapse()
        else:
            # Emit so app.py can populate the chapter data, then show
            self.clicked_sig.emit(self._index, self._title)
            # If we already have data, expand immediately
            if self._chunks:
                self._render_read_only()
            else:
                # Show a loading state while waiting for data
                self._show_loading()

    # ── Public state API ──────────────────────────────────────────────

    def set_state_running(self) -> None:
        self._regen_btn.setVisible(False)
        self._apply_dot("running")

    def set_state_done(self) -> None:
        self._apply_dot("done")
        self._regen_btn.setVisible(True)

    def set_state_error(self) -> None:
        self._apply_dot("error")
        self._regen_btn.setVisible(True)

    def set_state_pending(self) -> None:
        self._regen_btn.setVisible(False)
        self._apply_dot("pending")

    def set_regen_enabled(self, enabled: bool) -> None:
        self._regen_btn.setEnabled(enabled)

    def set_edit_allowed(self, allowed: bool) -> None:
        self._edit_allowed = allowed
        if self._expanded and not self._in_edit_mode and self._chunks:
            self._render_read_only()

    def refresh_if_expanded(self) -> None:
        if self._expanded and self._chunks and not self._in_edit_mode:
            self._render_read_only()

    def show_chapter_content(
        self,
        chunks: list[str],
        subdivision_type: str,
        title_announcement: str,
    ) -> None:
        self._chunks       = list(chunks)
        self._subdivision  = subdivision_type
        self._announcement = title_announcement
        self._in_edit_mode = False
        self._render_read_only()

    # ── Rendering ─────────────────────────────────────────────────────

    def _show_loading(self) -> None:
        self._clear_content()
        loading = QLabel("Loading chapter preview …")
        loading.setObjectName("preview-meta")
        self._content_layout.addWidget(loading)
        self._expand_visual()

    def _render_read_only(self) -> None:
        display_chunks = self._chunks

        self._clear_content()

        # Title announcement
        if self._announcement:
            ann = QFrame()
            ann.setObjectName("preview-announcement")
            al = QVBoxLayout(ann)
            al.setContentsMargins(10, 4, 6, 8)
            al.setSpacing(4)
            ann_hdr = QLabel("TITLE ANNOUNCEMENT")
            ann_hdr.setObjectName("preview-ann-header")
            al.addWidget(ann_hdr)
            ann_txt = QLabel(self._announcement)
            ann_txt.setObjectName("preview-ann-text")
            ann_txt.setWordWrap(True)
            al.addWidget(ann_txt)
            self._content_layout.addWidget(ann)

        # Meta row
        total_chars = sum(len(c) for c in display_chunks)
        chunk_word  = "chunk" if len(display_chunks) == 1 else "chunks"
        meta_text   = f"{len(display_chunks)} {chunk_word}  ·  {total_chars:,} characters"
        meta = QLabel(meta_text)
        meta.setObjectName("preview-meta")
        self._content_layout.addWidget(meta)

        # Up to 5 chunk cards
        max_shown = min(len(display_chunks), 5)
        for i, chunk in enumerate(display_chunks[:max_shown], start=1):
            card = QFrame()
            card.setObjectName("preview-chunk-card")
            ck = QVBoxLayout(card)
            ck.setContentsMargins(10, 6, 6, 6)
            ck.setSpacing(4)

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
            self._content_layout.addWidget(card)

        if len(display_chunks) > max_shown:
            more_lbl = QLabel(f"… and {len(display_chunks) - max_shown} more chunks")
            more_lbl.setObjectName("preview-meta")
            self._content_layout.addWidget(more_lbl)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        if self._edit_allowed:
            del_btn = QPushButton("🗑  Delete")
            del_btn.setObjectName("btn-delete-chapter")
            del_btn.clicked.connect(lambda: self.delete_clicked.emit(self._index))
            btn_row.addWidget(del_btn)
            edit_btn = QPushButton("✎  Edit")
            edit_btn.setObjectName("btn-edit-chapter")
            edit_btn.clicked.connect(self._enter_edit_mode)
            btn_row.addWidget(edit_btn)
        self._content_layout.addLayout(btn_row)

        self._expand_visual()

    def _enter_edit_mode(self) -> None:
        self._in_edit_mode = True
        self._clear_content()

        hint = QLabel("Edit text. Blank lines between paragraphs will be re-chunked on save.")
        hint.setObjectName("preview-meta")
        hint.setWordWrap(True)
        self._content_layout.addWidget(hint)

        # Title field
        title_lbl = QLabel("Chapter title:")
        title_lbl.setObjectName("preview-meta")
        self._content_layout.addWidget(title_lbl)
        self._title_edit = QLineEdit(self._title)
        self._title_edit.setObjectName("vd-spec-field")
        self._content_layout.addWidget(self._title_edit)

        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("chapter-text-edit")
        self._text_edit.setPlainText("\n\n".join(self._chunks))
        self._text_edit.setMinimumHeight(220)
        self._text_edit.textChanged.connect(self._update_char_count)
        self._content_layout.addWidget(self._text_edit)

        self._char_lbl = QLabel("")
        self._char_lbl.setObjectName("preview-meta")
        self._content_layout.addWidget(self._char_lbl)
        self._update_char_count()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn-edit-cancel")
        cancel_btn.clicked.connect(self._cancel_edit)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save & Re-chunk")
        save_btn.setObjectName("btn-edit-save")
        save_btn.clicked.connect(self._save_edit)
        btn_row.addWidget(save_btn)
        self._content_layout.addLayout(btn_row)

    def _update_char_count(self) -> None:
        if self._text_edit and self._char_lbl:
            n = len(self._text_edit.toPlainText())
            self._char_lbl.setText(f"{n:,} characters")

    def _cancel_edit(self) -> None:
        self._in_edit_mode = False
        self._render_read_only()

    def _save_edit(self) -> None:
        if self._text_edit is None:
            return
        new_title = (self._title_edit.text().strip() if self._title_edit else self._title) or self._title
        text = self._text_edit.toPlainText().strip()
        self._in_edit_mode = False
        # Update displayed title immediately
        self._title = new_title
        short = (new_title[:52] + "\u2026") if len(new_title) > 53 else new_title
        self._title_lbl.setText(short)
        self.edit_saved.emit(self._index, new_title, text)
        self._render_read_only()

    # ── Helpers ───────────────────────────────────────────────────────

    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                _delete_layout(item.layout())

    def _expand_visual(self) -> None:
        self._expanded = True
        self._expand_icon.setText("▾")
        self._inner_sep.setVisible(True)
        self._content.setVisible(True)
        self._hdr.setObjectName("exp-card-header-active")
        self._hdr.style().unpolish(self._hdr)
        self._hdr.style().polish(self._hdr)
        QTimer.singleShot(0, self._scroll_into_view)

    def _scroll_into_view(self) -> None:
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                parent.ensureWidgetVisible(self._content, 0, 20)
                break
            parent = parent.parent()

    def _collapse(self) -> None:
        self._expanded = False
        self._expand_icon.setText("▸")
        self._inner_sep.setVisible(False)
        self._content.setVisible(False)
        self._hdr.setObjectName("exp-card-header")
        self._hdr.style().unpolish(self._hdr)
        self._hdr.style().polish(self._hdr)

    def _apply_dot(self, state: str) -> None:
        self._dot.setObjectName(_DOT_OBJ[state])
        self._dot.style().unpolish(self._dot)
        self._dot.style().polish(self._dot)


def _delete_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            _delete_layout(item.layout())


class ChapterSection(QFrame):
    """Vertical chapter review section with expandable inline preview."""

    chapter_selected          = pyqtSignal(int, str)
    chapter_regen_requested   = pyqtSignal(int)
    chapter_edit_saved        = pyqtSignal(int, str, str)   # index, new_title, new_text
    chapter_delete_requested  = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("chapter-section")
        self._edit_allowed = False
        self._cards: dict[int, _ExpandableChapterCard] = {}
        self._expanded = True

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Section header ────────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("section-header")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 12, 16, 12)
        hl.setSpacing(10)

        self._toggle_btn = QPushButton("▾")
        self._toggle_btn.setObjectName("section-toggle-btn")
        self._toggle_btn.setFixedSize(22, 22)
        self._toggle_btn.clicked.connect(self._toggle_expand)
        hl.addWidget(self._toggle_btn)

        hdr_title = QLabel("CHAPTER REVIEW")
        hdr_title.setObjectName("section-title")
        hl.addWidget(hdr_title)
        hl.addStretch()

        self._count_lbl = QLabel("")
        self._count_lbl.setObjectName("pipeline-stage-lbl")
        hl.addWidget(self._count_lbl)

        root.addWidget(hdr)

        sep = QFrame()
        sep.setObjectName("panel-sep")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # ── Content: placeholder + cards ─────────────────────────────
        self._content = QWidget()
        self._content.setObjectName("section-content")
        cl = QVBoxLayout(self._content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        self._placeholder = QLabel(
            "No chapters yet — start processing a PDF to see chapters here."
        )
        self._placeholder.setObjectName("preview-placeholder")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setContentsMargins(20, 30, 20, 30)
        cl.addWidget(self._placeholder)

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(0)
        cl.addWidget(self._cards_widget)

        root.addWidget(self._content)

    # ── Toggle ────────────────────────────────────────────────────────

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._toggle_btn.setText("▾" if self._expanded else "▸")

    # ── Public API ────────────────────────────────────────────────────

    def load_chapters(self, chapters: list[tuple[int, str]]) -> None:
        self._clear_cards()
        for idx, title in chapters:
            self._add_card(idx, title)
        self._update_count()

    def add_chapters(self, chapters: list[tuple[int, str]]) -> None:
        for idx, title in chapters:
            if idx not in self._cards:
                self._add_card(idx, title)
        self._update_count()

    def clear(self) -> None:
        self._clear_cards()
        self._update_count()

    def set_running(self, chapter_idx: int) -> None:
        if card := self._cards.get(chapter_idx):
            card.set_state_running()

    def set_done(self, chapter_idx: int) -> None:
        if card := self._cards.get(chapter_idx):
            card.set_state_done()

    def set_error(self, chapter_idx: int) -> None:
        if card := self._cards.get(chapter_idx):
            card.set_state_error()

    def set_pending(self, chapter_idx: int) -> None:
        if card := self._cards.get(chapter_idx):
            card.set_state_pending()

    def set_regen_enabled_all(self, enabled: bool) -> None:
        for card in self._cards.values():
            card.set_regen_enabled(enabled)

    def set_edit_allowed(self, allowed: bool) -> None:
        self._edit_allowed = allowed
        for card in self._cards.values():
            card.set_edit_allowed(allowed)

    def remove_chapter(self, index: int) -> None:
        card = self._cards.pop(index, None)
        if card is not None:
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        if not self._cards:
            self._placeholder.setVisible(True)
        self._update_count()

    def refresh_all_expanded(self) -> None:
        for card in self._cards.values():
            card.refresh_if_expanded()

    def show_placeholder(self, message: str = "") -> None:
        pass  # chapters expand inline; no separate preview panel

    def show_chapter(
        self,
        index: int,
        title: str,
        chunks: list[str],
        subdivision_type: str,
        title_announcement: str,
    ) -> None:
        if card := self._cards.get(index):
            card.show_chapter_content(chunks, subdivision_type, title_announcement)

    # ── Internals ─────────────────────────────────────────────────────

    def _add_card(self, idx: int, title: str) -> None:
        self._placeholder.setVisible(False)
        card = _ExpandableChapterCard(idx, title)
        card.set_edit_allowed(self._edit_allowed)
        card.clicked_sig.connect(self._on_card_clicked)
        card.regen_clicked.connect(self.chapter_regen_requested)
        card.edit_saved.connect(self.chapter_edit_saved)
        card.delete_clicked.connect(self.chapter_delete_requested)
        self._cards[idx] = card
        self._cards_layout.addWidget(card)

    def _clear_cards(self) -> None:
        for card in list(self._cards.values()):
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        self._placeholder.setVisible(True)

    def _update_count(self) -> None:
        n = len(self._cards)
        self._count_lbl.setText(f"{n} chapters" if n else "")

    def _on_card_clicked(self, idx: int, title: str) -> None:
        self.chapter_selected.emit(idx, title)
