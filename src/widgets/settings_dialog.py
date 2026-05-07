"""Settings dialog — full .env configuration via UI."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
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

_S2PRO_REPO   = "fishaudio/s2-pro-gguf"
_S2PRO_FILES  = ["tokenizer.json", "s2-pro-q8_0.gguf"]
_S2PRO_LOCAL  = Path("checkpoints/s2-pro-gguf")


class _S2ProDownloader(QThread):
    status_msg = pyqtSignal(str)
    finished   = pyqtSignal(bool, str)   # success, message

    def __init__(self, dest: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dest = dest

    def run(self) -> None:
        try:
            from huggingface_hub import hf_hub_download
            self._dest.mkdir(parents=True, exist_ok=True)
            for fname in _S2PRO_FILES:
                self.status_msg.emit(f"Downloading {fname}…")
                hf_hub_download(_S2PRO_REPO, fname, local_dir=str(self._dest))
            self.finished.emit(True, "S2 Pro checkpoint downloaded.")
        except Exception as exc:
            self.finished.emit(False, str(exc))


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

        self._form = form  # needed for label lookups in _update_visibility

        # ── TTS ───────────────────────────────────────────────────────
        form.addRow(self._section_header("Text-to-Speech"))
        self._tts_backend = QComboBox()
        self._tts_backend.addItems(["fish_speech_cpp", "qwen_tts_clone"])
        self._tts_backend.setCurrentText(cfg.TTS_BACKEND)
        self._tts_backend.currentTextChanged.connect(self._update_visibility)
        form.addRow("TTS backend:", self._tts_backend)

        # S2 Pro checkpoint status + download (fish_speech_cpp only)
        self._s2pro_row_widget = QWidget()
        _hl = QHBoxLayout(self._s2pro_row_widget)
        _hl.setContentsMargins(0, 0, 0, 0)
        _hl.setSpacing(6)
        self._s2pro_status = QLabel()
        self._s2pro_status.setObjectName("settings-hint")
        _hl.addWidget(self._s2pro_status, stretch=1)
        self._s2pro_btn = QPushButton("Download (~5.6 GB)")
        self._s2pro_btn.setObjectName("browse-btn")
        self._s2pro_btn.clicked.connect(self._start_s2pro_download)
        _hl.addWidget(self._s2pro_btn)
        form.addRow("S2 Pro checkpoint:", self._s2pro_row_widget)
        self._refresh_s2pro_status()
        self._s2pro_worker: _S2ProDownloader | None = None

        self._tts_device = QComboBox()
        self._tts_device.addItems(["cuda", "cpu"])
        self._tts_device.setCurrentText(cfg.TTS_DEVICE if cfg.TTS_DEVICE in ["cuda", "cpu"] else "cuda")
        form.addRow("Device (VoiceDesign):", self._tts_device)
        self._tts_clone_model = self._line(
            form, "Clone model:",
            getattr(cfg, "TTS_CLONE_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-Base"),
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        )
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

        # Ollama-specific fields
        self._ollama_url = self._line(form, "Ollama URL:", cfg.OLLAMA_URL, "http://localhost:11434")
        self._llm_model  = self._line(form, "LLM model:", cfg.LLM_MODEL, "qwen3:8b")
        self._llm_ctx    = self._line(form, "Context window (tokens):", str(cfg.LLM_CTX), "16384")

        # OpenRouter-specific fields
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
        self._set_row_visible(self._ollama_url, enabled and is_ollama)
        self._set_row_visible(self._llm_model,  enabled and is_ollama)
        self._set_row_visible(self._llm_ctx,    enabled and is_ollama)
        self._set_row_visible(self._or_key,     enabled and not is_ollama)
        self._set_row_visible(self._or_model,   enabled and not is_ollama)
        is_clone    = self._tts_backend.currentText() == "qwen_tts_clone"
        is_fish_cpp = self._tts_backend.currentText() == "fish_speech_cpp"
        self._set_row_visible(self._tts_clone_model,   is_clone)
        self._set_row_visible(self._s2pro_row_widget,  is_fish_cpp)

    def _set_row_visible(self, field: QWidget, visible: bool) -> None:
        """Show or hide a form row (label + field) by field widget."""
        field.setVisible(visible)
        lbl = self._form.labelForField(field)
        if lbl:
            lbl.setVisible(visible)

    def _refresh_s2pro_status(self) -> None:
        gguf = _S2PRO_LOCAL / "s2-pro-q8_0.gguf"
        tok  = _S2PRO_LOCAL / "tokenizer.json"
        if gguf.exists() and tok.exists():
            self._s2pro_status.setText("Present")
            self._s2pro_status.setStyleSheet("color: #4caf50;")
            self._s2pro_btn.setText("Re-download")
        else:
            self._s2pro_status.setText("Missing")
            self._s2pro_status.setStyleSheet("color: #ff9800;")
            self._s2pro_btn.setText("Download (~5.6 GB)")

    def _start_s2pro_download(self) -> None:
        if self._s2pro_worker and self._s2pro_worker.isRunning():
            return
        self._s2pro_btn.setEnabled(False)
        self._s2pro_status.setStyleSheet("")
        self._s2pro_worker = _S2ProDownloader(_S2PRO_LOCAL, self)
        self._s2pro_worker.status_msg.connect(self._s2pro_status.setText)
        self._s2pro_worker.finished.connect(self._on_s2pro_done)
        self._s2pro_worker.start()

    def _on_s2pro_done(self, ok: bool, msg: str) -> None:
        self._s2pro_btn.setEnabled(True)
        if ok:
            import src.config as cfg
            cfg.FISH_SPEECH_CPP_MODEL     = str(_S2PRO_LOCAL / "s2-pro-q8_0.gguf")
            cfg.FISH_SPEECH_CPP_TOKENIZER = str(_S2PRO_LOCAL / "tokenizer.json")
            _persist_env({
                "FISH_SPEECH_CPP_MODEL":     cfg.FISH_SPEECH_CPP_MODEL,
                "FISH_SPEECH_CPP_TOKENIZER": cfg.FISH_SPEECH_CPP_TOKENIZER,
            })
        self._refresh_s2pro_status()
        if not ok:
            self._s2pro_status.setText(f"Error: {msg}")
            self._s2pro_status.setStyleSheet("color: #f44336;")

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
        cfg.TTS_BACKEND        = self._tts_backend.currentText()
        cfg.TTS_DEVICE         = self._tts_device.currentText()
        if hasattr(cfg, "TTS_CLONE_MODEL"):
            cfg.TTS_CLONE_MODEL = s(self._tts_clone_model) or cfg.TTS_CLONE_MODEL
        try:
            cfg.TTS_CHUNK_SIZE = int(s(self._tts_chunk))
        except ValueError:
            pass
        cfg.TTS_VOICE_INSTRUCT = s(self._tts_voice_instruct) or cfg.TTS_VOICE_INSTRUCT
        cfg.OUTPUT_DIR         = Path(s(self._output_dir) or str(cfg.OUTPUT_DIR))
        cfg.ADAPTATION_ENABLED  = self._adapt_enabled.isChecked()
        cfg.ADAPTATION_PROVIDER = self._provider_combo.currentText()
        cfg.OPENROUTER_API_KEY  = s(self._or_key)
        cfg.OPENROUTER_MODEL    = s(self._or_model)    or cfg.OPENROUTER_MODEL

        seed_str = s(self._tts_seed)
        if hasattr(cfg, "TTS_SEED"):
            cfg.TTS_SEED = int(seed_str) if seed_str.isdigit() else None

        _persist_env({
            "OLLAMA_URL":          cfg.OLLAMA_URL,
            "LLM_MODEL":           cfg.LLM_MODEL,
            "LLM_CTX":             str(cfg.LLM_CTX),
            "TTS_BACKEND":         cfg.TTS_BACKEND,
            "TTS_CLONE_MODEL":      s(self._tts_clone_model),
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
