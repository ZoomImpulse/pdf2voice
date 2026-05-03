"""pdf2voice — Info bar: three side-by-side cards at the top of the window."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.config import LLM_MODEL, OUTPUT_DIR, TTS_BASE_MODEL, TTS_DESIGN_MODEL, TTS_GENDER


class InfoBar(QFrame):
    """Horizontal row of three info/config cards."""

    def __init__(self, initial_path: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("info-bar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._make_pdf_card(initial_path), stretch=3)
        layout.addWidget(self._make_voice_card(), stretch=1)
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

    def _make_voice_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("info-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel("🎙  VOICE")
        title.setObjectName("info-card-title")
        layout.addWidget(title)

        # Segmented pill toggle
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(0)
        toggle_row.setContentsMargins(0, 0, 0, 0)

        self._btn_female = QPushButton("♀  Female")
        self._btn_female.setObjectName("voice-pill-left")
        self._btn_female.setCheckable(True)
        self._btn_female.setFixedHeight(34)
        self._btn_female.clicked.connect(lambda: self._select_gender("female"))

        self._btn_male = QPushButton("♂  Male")
        self._btn_male.setObjectName("voice-pill-right")
        self._btn_male.setCheckable(True)
        self._btn_male.setFixedHeight(34)
        self._btn_male.clicked.connect(lambda: self._select_gender("male"))

        self._select_gender(TTS_GENDER)

        toggle_row.addWidget(self._btn_female)
        toggle_row.addWidget(self._btn_male)
        layout.addLayout(toggle_row)
        layout.addStretch()

        return card

    def _select_gender(self, gender: str) -> None:
        self._btn_female.setChecked(gender == "female")
        self._btn_male.setChecked(gender == "male")
        self._btn_female.setObjectName(
            "voice-pill-left-active" if gender == "female" else "voice-pill-left"
        )
        self._btn_male.setObjectName(
            "voice-pill-right-active" if gender == "male" else "voice-pill-right"
        )
        for btn in (self._btn_female, self._btn_male):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

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
        base_short   = TTS_BASE_MODEL.split("/")[-1]
        for key, val in [
            ("LLM",    LLM_MODEL),
            ("Anchor", design_short),
            ("Base",   base_short),
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

    # ── Public API ────────────────────────────────────────────────────

    def get_pdf_path(self) -> str:
        return self._path_edit.text().strip()

    def get_gender(self) -> str:
        return "female" if self._btn_female.isChecked() else "male"

    def set_pdf_info(self, info: str) -> None:
        if info:
            self._pdf_info_lbl.setText(info)
            self._pdf_info_lbl.setVisible(True)
        else:
            self._pdf_info_lbl.setVisible(False)

    def set_controls_enabled(self, enabled: bool) -> None:
        self._path_edit.setEnabled(enabled)
        self._browse_btn.setEnabled(enabled)
        self._btn_female.setEnabled(enabled)
        self._btn_male.setEnabled(enabled)
