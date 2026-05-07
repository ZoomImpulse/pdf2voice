"""pdf2voice — Info bar: three side-by-side cards at the top of the window."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.config import LLM_MODEL, OUTPUT_DIR, TTS_DESIGN_MODEL


class InfoBar(QFrame):
    """Horizontal row of three info/config cards."""

    pdf_selected = pyqtSignal(str)  # emitted when the user picks a PDF via Browse

    def __init__(self, initial_path: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("info-bar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._make_pdf_card(initial_path), stretch=3)
        layout.addWidget(self._make_config_card(), stretch=2)

    # ── Card builders ─────────────────────────────────────────────────

    def _make_pdf_card(self, initial_path: str) -> QFrame:
        card = QFrame()
        card.setObjectName("info-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel("📄  PDF FILE")
        title.setObjectName("info-card-title")
        layout.addWidget(title)

        self._path_edit = QLineEdit(initial_path)
        self._path_edit.setObjectName("path-edit")
        self._path_edit.setPlaceholderText("Path to PDF file …")
        self._path_edit.setReadOnly(True)
        layout.addWidget(self._path_edit)

        self._browse_btn = QPushButton("Browse …")
        self._browse_btn.setObjectName("browse-btn")
        self._browse_btn.clicked.connect(self._browse)
        layout.addWidget(self._browse_btn)

        self._pdf_info_lbl = QLabel("")
        self._pdf_info_lbl.setObjectName("info-card-meta")
        self._pdf_info_lbl.setVisible(False)
        layout.addWidget(self._pdf_info_lbl)

        return card

    def _make_config_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("info-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        title = QLabel("CONFIG")
        title.setObjectName("info-card-title")
        layout.addWidget(title)

        design_short = TTS_DESIGN_MODEL.split("/")[-1]
        for key, val in [
            ("LLM",    LLM_MODEL),
            ("Design", design_short),
            ("Output", str(OUTPUT_DIR)),
        ]:
            row = QHBoxLayout()
            row.setSpacing(6)
            k = QLabel(key + ":")
            k.setObjectName("settings-key")
            k.setFixedWidth(48)
            v = QLabel(val)
            v.setObjectName("settings-val")
            v.setWordWrap(True)
            row.addWidget(k)
            row.addWidget(v, stretch=1)
            layout.addLayout(row)

        return card

    # ── Actions ───────────────────────────────────────────────────────

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF files (*.pdf);;All files (*.*)"
        )
        if path:
            self._path_edit.setText(path)
            self.pdf_selected.emit(path)

    # ── Public API ────────────────────────────────────────────────────

    def get_pdf_path(self) -> str:
        return self._path_edit.text().strip()

    def set_pdf_path(self, path: str) -> None:
        self._path_edit.setText(path)

    def set_pdf_info(self, info: str) -> None:
        if info:
            self._pdf_info_lbl.setText(info)
            self._pdf_info_lbl.setVisible(True)
        else:
            self._pdf_info_lbl.setVisible(False)

    def set_controls_enabled(self, enabled: bool) -> None:
        self._browse_btn.setEnabled(enabled)
