"""Settings dialog — full .env configuration via UI."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(560)
        self.setMinimumHeight(600)
        self.setModal(True)

        import src.config as cfg
        self._cfg = cfg

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setSpacing(0)
        body_layout.setContentsMargins(20, 20, 20, 20)
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        # Single form layout — all rows share one label column
        form = QFormLayout()
        form.setSpacing(10)
        form.setContentsMargins(0, 0, 0, 0)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        body_layout.addLayout(form)
        body_layout.addStretch()

        # ── LLM / Ollama ──────────────────────────────────────────────
        form.addRow(self._section_header("LLM / Ollama"))
        self._ollama_url = self._line(form, "Ollama URL:", cfg.OLLAMA_URL, "http://localhost:11434")
        self._llm_model  = self._line(form, "LLM model:", cfg.LLM_MODEL, "qwen3:8b")
        self._llm_ctx    = self._line(form, "Context window (tokens):", str(cfg.LLM_CTX), "16384")

        # ── TTS ───────────────────────────────────────────────────────
        form.addRow(self._section_header("Text-to-Speech"))
        self._tts_device = QComboBox()
        self._tts_device.addItems(["cuda", "cuda:0", "cuda:1", "cpu"])
        current_device = cfg.TTS_DEVICE if cfg.TTS_DEVICE in ["cuda", "cuda:0", "cuda:1", "cpu"] else "cuda"
        self._tts_device.setCurrentText(current_device)
        form.addRow("Device:", self._tts_device)
        self._tts_chunk  = self._line(form, "Chunk size (chars):", str(cfg.TTS_CHUNK_SIZE), "3000")
        seed_val = str(cfg.TTS_SEED) if getattr(cfg, "TTS_SEED", None) is not None else ""
        self._tts_seed   = self._line(form, "Seed (blank = auto):", seed_val, "")
        self._output_dir, _ = self._browse_row(
            form, "Output directory:", str(cfg.OUTPUT_DIR), directory=True
        )

        # ── Voice ─────────────────────────────────────────────────────
        form.addRow(self._section_header("Voice"))
        self._tts_voice_instruct = QLineEdit(cfg.TTS_VOICE_INSTRUCT)
        self._tts_voice_instruct.setObjectName("settings-input")
        self._tts_voice_instruct.setPlaceholderText("Audiobook narrator style …")
        form.addRow("Voice instruction:", self._tts_voice_instruct)
        self._tts_speaker   = self._line(form, "Speaker (CustomVoice):", getattr(cfg, "TTS_SPEAKER", ""), "Vivian")
        self._tts_ref_audio, _ = self._browse_row(
            form, "Ref. audio path:", getattr(cfg, "TTS_REF_AUDIO", ""),
            file_filter="Audio files (*.wav *.mp3 *.flac *.ogg)"
        )
        self._tts_ref_text, _ = self._browse_row(
            form, "Ref. audio transcript:", getattr(cfg, "TTS_REF_TEXT", ""),
            file_filter="Text files (*.txt)"
        )

        # ── Audiobook Adaptation ──────────────────────────────────────
        form.addRow(self._section_header("Audiobook Adaptation"))

        self._adapt_enabled = QPushButton()
        self._adapt_enabled.setCheckable(True)
        self._adapt_enabled.setChecked(cfg.ADAPTATION_ENABLED)
        self._adapt_enabled.setObjectName("toggle-btn")
        self._adapt_enabled.setText("ON" if cfg.ADAPTATION_ENABLED else "OFF")
        self._adapt_enabled.toggled.connect(self._on_adapt_toggled)
        form.addRow("Enable adaptation:", self._adapt_enabled)

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["ollama", "openrouter"])
        self._provider_combo.setCurrentText(cfg.ADAPTATION_PROVIDER)
        self._provider_combo.currentTextChanged.connect(self._update_visibility)
        form.addRow("Provider:", self._provider_combo)

        self._adapt_model = self._line(form, "Ollama adapt model:", cfg.ADAPTATION_MODEL, "qwen3:8b")

        self._or_key = QLineEdit(cfg.OPENROUTER_API_KEY)
        self._or_key.setPlaceholderText("sk-or-…")
        self._or_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._or_key.setObjectName("settings-input")
        form.addRow("OpenRouter key:", self._or_key)

        self._or_model = self._line(form, "OpenRouter model:", cfg.OPENROUTER_MODEL, "deepseek/deepseek-v4-flash")

        # ── Hint + buttons ────────────────────────────────────────────
        footer = QWidget()
        fl2 = QVBoxLayout(footer)
        fl2.setContentsMargins(20, 8, 20, 16)
        fl2.setSpacing(10)

        hint = QLabel("Changes are saved to <code>.env</code> and applied immediately.")
        hint.setObjectName("settings-hint")
        hint.setTextFormat(Qt.TextFormat.RichText)
        fl2.addWidget(hint)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        fl2.addWidget(btns)
        root.addWidget(footer)

        self._update_visibility()

    # ── Helpers ───────────────────────────────────────────────────────

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setObjectName("settings-section")
        return lbl

    def _line(self, fl: QFormLayout, label: str, value: str, placeholder: str) -> QLineEdit:
        w = QLineEdit(value)
        w.setPlaceholderText(placeholder)
        w.setObjectName("settings-input")
        fl.addRow(label, w)
        return w

    def _browse_row(
        self,
        fl: QFormLayout,
        label: str,
        value: str,
        *,
        directory: bool = False,
        file_filter: str = "",
    ) -> tuple[QLineEdit, QPushButton]:
        """Line edit + Browse button row."""
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)
        edit = QLineEdit(value)
        edit.setObjectName("settings-input")
        hl.addWidget(edit, stretch=1)
        btn = QPushButton("Browse…")
        btn.setFixedWidth(80)
        btn.setObjectName("browse-btn")
        if directory:
            btn.clicked.connect(lambda: self._pick_dir(edit))
        else:
            btn.clicked.connect(lambda: self._pick_file(edit, file_filter))
        hl.addWidget(btn)
        fl.addRow(label, row)
        return edit, btn

    def _pick_dir(self, edit: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select directory", edit.text() or "."
        )
        if path:
            edit.setText(path)

    def _pick_file(self, edit: QLineEdit, file_filter: str) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select file", edit.text() or ".", file_filter or "All files (*)"
        )
        if path:
            edit.setText(path)

    # ── Logic ─────────────────────────────────────────────────────────

    def _on_adapt_toggled(self, checked: bool) -> None:
        self._adapt_enabled.setText("ON" if checked else "OFF")
        self._update_visibility()

    def _update_visibility(self) -> None:
        enabled   = self._adapt_enabled.isChecked()
        is_ollama = self._provider_combo.currentText() == "ollama"
        self._provider_combo.setEnabled(enabled)
        self._adapt_model.setEnabled(enabled and is_ollama)
        self._or_key.setEnabled(enabled and not is_ollama)
        self._or_model.setEnabled(enabled and not is_ollama)

    def _save(self) -> None:
        import src.config as cfg

        def s(w: QLineEdit) -> str:
            return w.text().strip()

        cfg.OLLAMA_URL         = s(self._ollama_url)  or cfg.OLLAMA_URL
        cfg.LLM_MODEL          = s(self._llm_model)   or cfg.LLM_MODEL
        try:
            cfg.LLM_CTX        = int(s(self._llm_ctx))
        except ValueError:
            pass
        cfg.TTS_DEVICE         = self._tts_device.currentText()
        try:
            cfg.TTS_CHUNK_SIZE = int(s(self._tts_chunk))
        except ValueError:
            pass
        cfg.TTS_VOICE_INSTRUCT = s(self._tts_voice_instruct) or cfg.TTS_VOICE_INSTRUCT
        cfg.OUTPUT_DIR         = Path(s(self._output_dir) or str(cfg.OUTPUT_DIR))
        cfg.ADAPTATION_ENABLED  = self._adapt_enabled.isChecked()
        cfg.ADAPTATION_PROVIDER = self._provider_combo.currentText()
        cfg.ADAPTATION_MODEL    = s(self._adapt_model) or cfg.ADAPTATION_MODEL
        cfg.OPENROUTER_API_KEY  = s(self._or_key)
        cfg.OPENROUTER_MODEL    = s(self._or_model)    or cfg.OPENROUTER_MODEL

        seed_str = s(self._tts_seed)
        if hasattr(cfg, "TTS_SEED"):
            cfg.TTS_SEED = int(seed_str) if seed_str.isdigit() else None

        _persist_env({
            "OLLAMA_URL":          cfg.OLLAMA_URL,
            "LLM_MODEL":           cfg.LLM_MODEL,
            "LLM_CTX":             str(cfg.LLM_CTX),
            "TTS_DEVICE":          cfg.TTS_DEVICE,
            "TTS_CHUNK_SIZE":      str(cfg.TTS_CHUNK_SIZE),
            "TTS_SEED":            seed_str,
            "TTS_VOICE_INSTRUCT":  cfg.TTS_VOICE_INSTRUCT,
            "TTS_SPEAKER":         s(self._tts_speaker),
            "TTS_REF_AUDIO":       s(self._tts_ref_audio),
            "TTS_REF_TEXT":        s(self._tts_ref_text),
            "OUTPUT_DIR":          str(cfg.OUTPUT_DIR),
            "ADAPTATION_ENABLED":  str(cfg.ADAPTATION_ENABLED).lower(),
            "ADAPTATION_PROVIDER": cfg.ADAPTATION_PROVIDER,
            "ADAPTATION_MODEL":    cfg.ADAPTATION_MODEL,
            "OPENROUTER_API_KEY":  cfg.OPENROUTER_API_KEY,
            "OPENROUTER_MODEL":    cfg.OPENROUTER_MODEL,
        })
        self.accept()


def _persist_env(updates: dict[str, str]) -> None:
    """Write changed keys back to .env — preserves comments and unrelated lines."""
    env_path = Path(".env")
    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    written: set[str] = set()
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            result.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            result.append(f"{key}={updates[key]}")
            written.add(key)
        else:
            result.append(line)

    for key, val in updates.items():
        if key not in written:
            result.append(f"{key}={val}")

    env_path.write_text("\n".join(result) + "\n", encoding="utf-8")
