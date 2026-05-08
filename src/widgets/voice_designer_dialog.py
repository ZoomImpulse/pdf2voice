"""Voice Designer dialog — structured per-genre voice spec editor."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import json

from src.config import (
    GENRE_PROMPTS,
    GENRE_VOICE_SPECS,
    VOICE_ANCHORS_DIR,
    VOICE_SPEC_FIELDS,
    format_voice_spec,
)

_VOICE_SPECS_FILE: Path = VOICE_ANCHORS_DIR / "voice_specs.json"
from src.workers import VoiceDesignWorker, VoiceFillWorker

_GREEN_DOT = "●"
_GREY_DOT  = "○"

_GENRES: list[str] = list(GENRE_PROMPTS.keys())

_LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    ("en", "EN — English"),
    ("de", "DE — Deutsch"),
]

_GENDER_OPTIONS: list[str] = ["Female", "Male", "Neutral"]
_AGE_OPTIONS:    list[str] = ["Child", "Teen", "Young Adult", "Adult", "Middle-aged", "Senior"]

_FIELD_LABELS: dict[str, str] = {
    "gender":      "Gender",
    "pitch":       "Pitch",
    "speed":       "Speed",
    "volume":      "Volume",
    "age":         "Age",
    "clarity":     "Clarity",
    "fluency":     "Fluency",
    "accent":      "Accent",
    "texture":     "Texture",
    "emotion":     "Emotion",
    "tone":        "Tone",
    "personality": "Personality",
}


class VoiceDesignerDialog(QDialog):
    def __init__(self, initial_genre: str = "", initial_language: str = "en", parent=None) -> None:
        super().__init__(parent)
        self._initial_genre    = initial_genre
        self._language         = initial_language
        self._worker: VoiceDesignWorker | None = None
        self._preview_path: Path | None = None
        self._watcher: _PlaybackWatcher | None = None
        self._spec_fields: dict[str, QLineEdit | QComboBox] = {}
        self._edited_specs: dict[str, dict[str, str]] = self._load_specs_from_disk()
        self._fill_worker: VoiceFillWorker | None = None

        self.setWindowTitle("Voice Designer")
        self.setModal(True)
        self.setMinimumSize(820, 620)
        self._build_ui()

    # ── Persistent spec storage ──────────────────────────────────────────────

    @staticmethod
    def _load_specs_from_disk() -> dict[str, dict[str, str]]:
        try:
            if _VOICE_SPECS_FILE.is_file():
                return json.loads(_VOICE_SPECS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _persist_specs_to_disk(self) -> None:
        try:
            _VOICE_SPECS_FILE.write_text(
                json.dumps(self._edited_specs, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._make_genre_panel())
        body_layout.addWidget(self._make_detail_panel(), stretch=1)
        root.addWidget(body, stretch=1)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #1e1e2e;")
        root.addWidget(sep)

        footer = QWidget()
        footer.setFixedHeight(52)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(20, 0, 20, 0)
        fl.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("vd-close-btn")
        close_btn.clicked.connect(self.accept)
        fl.addWidget(close_btn)
        root.addWidget(footer)

        start_row = _GENRES.index(self._initial_genre) if self._initial_genre in _GENRES else 0
        if _GENRES:
            self._genre_list.setCurrentRow(start_row)

    def _make_genre_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("vd-genre-panel")
        panel.setFixedWidth(210)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        header = QLabel("GENRES")
        header.setObjectName("settings-section")
        layout.addWidget(header)

        self._genre_list = QListWidget()
        self._genre_list.setObjectName("vd-genre-list")
        self._genre_list.currentRowChanged.connect(self._on_genre_selected)
        layout.addWidget(self._genre_list)
        self._refresh_genre_list()
        return panel

    def _make_detail_panel(self) -> QWidget:
        panel = QWidget()
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(10)

        # Genre title + language selector
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(10)

        self._title_lbl = QLabel("")
        self._title_lbl.setObjectName("vd-genre-title")
        title_row.addWidget(self._title_lbl, stretch=1)

        lang_lbl = QLabel("Language:")
        lang_lbl.setObjectName("vd-spec-label")
        title_row.addWidget(lang_lbl)

        self._lang_combo = QComboBox()
        self._lang_combo.setObjectName("genre-combo")
        self._lang_combo.setFixedHeight(30)
        self._lang_combo.setMinimumWidth(130)
        for code, label in _LANGUAGE_OPTIONS:
            self._lang_combo.addItem(label, userData=code)
        # Pre-select the language passed to the constructor
        init_idx = next(
            (i for i, (c, _) in enumerate(_LANGUAGE_OPTIONS) if c == self._language), 0
        )
        self._lang_combo.setCurrentIndex(init_idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        title_row.addWidget(self._lang_combo)

        outer.addLayout(title_row)

        # AI Fill row
        ai_row = QHBoxLayout()
        ai_row.setContentsMargins(0, 0, 0, 0)
        ai_row.setSpacing(6)
        self._ai_prompt_input = QLineEdit()
        self._ai_prompt_input.setObjectName("vd-ai-prompt")
        self._ai_prompt_input.setPlaceholderText("Describe the voice… (e.g. warm elderly British male)")
        self._ai_fill_btn = QPushButton("✨ AI Fill")
        self._ai_fill_btn.setObjectName("vd-ai-fill-btn")
        self._ai_fill_btn.setFixedWidth(100)
        self._ai_fill_btn.clicked.connect(self._on_ai_fill_clicked)
        ai_row.addWidget(self._ai_prompt_input, stretch=1)
        ai_row.addWidget(self._ai_fill_btn)
        outer.addLayout(ai_row)

        # Scrollable spec form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        form_widget = QWidget()
        form_widget.setStyleSheet("background: transparent;")
        form = QFormLayout(form_widget)
        form.setContentsMargins(0, 4, 8, 4)
        form.setSpacing(6)
        form.setLabelAlignment(
            __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignRight
        )

        for field in VOICE_SPEC_FIELDS:
            lbl = QLabel(_FIELD_LABELS[field] + ":")
            lbl.setObjectName("vd-spec-label")
            if field == "gender":
                widget: QLineEdit | QComboBox = QComboBox()
                widget.setObjectName("vd-spec-combo")
                widget.addItems(_GENDER_OPTIONS)
            elif field == "age":
                widget = QComboBox()
                widget.setObjectName("vd-spec-combo")
                widget.addItems(_AGE_OPTIONS)
            else:
                widget = QLineEdit()
                widget.setObjectName("vd-spec-field")
                widget.setPlaceholderText(f"{field} …")
            self._spec_fields[field] = widget
            form.addRow(lbl, widget)

        scroll.setWidget(form_widget)
        outer.addWidget(scroll, stretch=1)

        # Reset-prompt button (right-aligned)
        rp_row = QHBoxLayout()
        rp_row.setContentsMargins(0, 0, 0, 0)
        rp_row.addStretch()
        self._reset_prompt_btn = QPushButton("↺  Reset to default")
        self._reset_prompt_btn.setObjectName("vd-reset-prompt-btn")
        self._reset_prompt_btn.clicked.connect(self._on_reset_prompt_clicked)
        rp_row.addWidget(self._reset_prompt_btn)
        outer.addLayout(rp_row)

        # Status row
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(6)
        self._status_dot_lbl = QLabel(_GREY_DOT)
        self._status_dot_lbl.setStyleSheet("color: #2d3748; font-size: 14px;")
        self._status_text_lbl = QLabel("No saved voice — click Generate to create one.")
        self._status_text_lbl.setObjectName("vd-status-text")
        status_row.addWidget(self._status_dot_lbl)
        status_row.addWidget(self._status_text_lbl, stretch=1)
        outer.addLayout(status_row)

        # Progress bar (hidden when idle)
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("vd-progress")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.hide()
        outer.addWidget(self._progress_bar)

        # Log message (hidden when idle)
        self._log_lbl = QLabel("")
        self._log_lbl.setObjectName("vd-log-msg")
        self._log_lbl.hide()
        outer.addWidget(self._log_lbl)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 4, 0, 0)
        btn_row.setSpacing(8)

        self._generate_btn = QPushButton("Generate")
        self._generate_btn.setObjectName("header-btn")
        self._generate_btn.clicked.connect(self._on_generate_clicked)
        btn_row.addWidget(self._generate_btn)

        self._replay_btn = QPushButton("▶  Replay")
        self._replay_btn.setObjectName("vd-replay-btn")
        self._replay_btn.setEnabled(False)
        self._replay_btn.clicked.connect(self._on_replay_clicked)
        btn_row.addWidget(self._replay_btn)


        self._use_btn = QPushButton("Use This Voice")
        self._use_btn.setObjectName("vd-use-btn")
        self._use_btn.setEnabled(False)
        self._use_btn.clicked.connect(self._on_use_this_voice_clicked)
        btn_row.addWidget(self._use_btn)

        self._reset_btn = QPushButton("Reset Voice")
        self._reset_btn.setObjectName("vd-reset-btn")
        self._reset_btn.setEnabled(False)
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        btn_row.addWidget(self._reset_btn)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        return panel

    # ── Genre selection ───────────────────────────────────────────────────────

    @pyqtSlot(int)
    def _on_genre_selected(self, row: int) -> None:
        if row < 0 or row >= len(_GENRES):
            return
        # Save edits for the previously selected genre before switching.
        prev_row = self._genre_list.property("_prev_row")
        if prev_row is not None and 0 <= prev_row < len(_GENRES):
            self._save_spec_fields(_GENRES[prev_row])
        self._genre_list.setProperty("_prev_row", row)

        genre = _GENRES[row]
        self._title_lbl.setText(genre.capitalize())
        self._populate_spec_fields(genre)

        has_anchor = self._anchor_path_for(genre).is_file()
        self._update_status(genre, has_anchor)
        self._replay_btn.setEnabled(False)
        self._use_btn.setEnabled(False)
        self._reset_btn.setEnabled(has_anchor)

        self._preview_path = None

    def _save_spec_fields(self, genre: str) -> None:
        self._edited_specs[genre] = {
            f: (
                w.currentText() if isinstance(w, QComboBox) else w.text().strip()  # type: ignore[union-attr]
            )
            for f, w in self._spec_fields.items()
        }
        self._persist_specs_to_disk()

    def _populate_spec_fields(self, genre: str) -> None:
        spec = self._edited_specs.get(genre) or GENRE_VOICE_SPECS.get(genre, {})
        for field, widget in self._spec_fields.items():
            value = spec.get(field, "")
            if isinstance(widget, QComboBox):
                widget.setCurrentText(value)
            else:
                widget.setText(value)

    # ── AI Fill ───────────────────────────────────────────────────────────────

    @pyqtSlot()
    def _on_ai_fill_clicked(self) -> None:
        prompt = self._ai_prompt_input.text().strip()
        if not prompt:
            self._log_lbl.setText("Enter a voice description first.")
            self._log_lbl.show()
            return

        from src.config import (
            ADAPTATION_PROVIDER,
            OPENROUTER_API_KEY,
            OPENROUTER_MODEL,
            OLLAMA_URL,
            LLM_MODEL,
        )

        model = OPENROUTER_MODEL if ADAPTATION_PROVIDER == "openrouter" else LLM_MODEL

        self._ai_fill_btn.setEnabled(False)
        self._ai_fill_btn.setText("Filling…")
        self._progress_bar.setRange(0, 0)  # indeterminate
        self._progress_bar.show()
        self._log_lbl.setText(f"Asking {ADAPTATION_PROVIDER} to fill voice spec…")
        self._log_lbl.show()

        self._fill_worker = VoiceFillWorker(
            prompt=prompt,
            provider=ADAPTATION_PROVIDER,
            model=model,
            api_key=OPENROUTER_API_KEY,
            ollama_base_url=OLLAMA_URL,
        )
        self._fill_worker.filled.connect(self._on_fill_complete)
        self._fill_worker.failed.connect(self._on_fill_error)
        self._fill_worker.start()

    @pyqtSlot(dict)
    def _on_fill_complete(self, spec: dict) -> None:
        for field, widget in self._spec_fields.items():
            value = spec.get(field, "")
            if not value:
                continue
            if isinstance(widget, QComboBox):
                # Only apply if the value is one of the allowed options
                if widget.findText(str(value)) >= 0:
                    widget.setCurrentText(str(value))
            else:
                widget.setText(str(value))  # type: ignore[union-attr]

        # Persist the filled values immediately so a genre/language switch doesn't discard them
        genre = self._current_genre()
        if genre:
            self._save_spec_fields(genre)

        self._progress_bar.setRange(0, 100)
        self._progress_bar.hide()
        self._log_lbl.setText("✓ Form filled by AI — review and click Generate.")
        self._ai_fill_btn.setText("✨ AI Fill")
        self._ai_fill_btn.setEnabled(True)

    @pyqtSlot(str)
    def _on_fill_error(self, msg: str) -> None:
        self._progress_bar.setRange(0, 100)
        self._progress_bar.hide()
        self._log_lbl.setText(f"AI Fill error: {msg}")
        self._ai_fill_btn.setText("✨ AI Fill")
        self._ai_fill_btn.setEnabled(True)

    # ── Generate ──────────────────────────────────────────────────────────────

    @pyqtSlot()
    def _on_generate_clicked(self) -> None:
        genre = self._current_genre()
        if genre is None:
            return
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)

        # Persist the current field values before generating so reopening the
        # dialog always shows the spec that matches the active voice anchor.
        self._save_spec_fields(genre)

        self._generate_btn.setEnabled(False)
        self._replay_btn.setEnabled(False)
        self._use_btn.setEnabled(False)
        self._reset_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._progress_bar.show()
        self._log_lbl.setText("Starting …")
        self._log_lbl.show()

        voice_instruct = format_voice_spec(
            {
                f: (
                    self._spec_fields[f].currentText()
                    if isinstance(self._spec_fields[f], QComboBox)
                    else self._spec_fields[f].text().strip()  # type: ignore[union-attr]
                )
                for f in VOICE_SPEC_FIELDS
            }
        )
        self._worker = VoiceDesignWorker(genre=genre, language=self._language, voice_instruct=voice_instruct)
        self._worker.log.connect(self._on_worker_log)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.finished_ok.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.start()

    # ── Worker slots ──────────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_worker_log(self, msg: str) -> None:
        self._log_lbl.setText(msg)

    @pyqtSlot(float)
    def _on_worker_progress(self, pct: float) -> None:
        self._progress_bar.setValue(int(pct))

    @pyqtSlot(object)
    def _on_worker_finished(self, path: object) -> None:
        self._preview_path = path  # type: ignore[assignment]
        self._progress_bar.setValue(100)
        self._progress_bar.hide()
        self._log_lbl.setText("Ready — playing preview …")

        genre = self._current_genre()
        if genre:
            self._update_status(genre, has_anchor=True)
            self._refresh_genre_list()

        self._generate_btn.setEnabled(True)
        self._replay_btn.setEnabled(True)
        self._use_btn.setEnabled(True)
        self._reset_btn.setEnabled(True)
        self._play_wav(path)  # type: ignore[arg-type]

    @pyqtSlot(str)
    def _on_worker_failed(self, msg: str) -> None:
        self._progress_bar.hide()
        self._log_lbl.setText(f"Error: {msg}")
        self._generate_btn.setEnabled(True)
        genre = self._current_genre()
        if genre:
            self._reset_btn.setEnabled(self._anchor_path_for(genre).is_file())

    # ── Replay / Use / Reset ──────────────────────────────────────────────────

    @pyqtSlot()
    def _on_replay_clicked(self) -> None:
        if self._preview_path:
            self._play_wav(self._preview_path)

    @pyqtSlot()
    def _on_use_this_voice_clicked(self) -> None:
        genre = self._current_genre()
        if genre is None:
            return
        self._refresh_genre_list()
        self._update_status(genre, has_anchor=True, confirmed=True)
        self._use_btn.setEnabled(False)

    @pyqtSlot()
    def _on_reset_prompt_clicked(self) -> None:
        genre = self._current_genre()
        if genre:
            self._edited_specs.pop(genre, None)  # discard edits so defaults are loaded
            self._persist_specs_to_disk()
            self._populate_spec_fields(genre)

    @pyqtSlot()
    def _on_reset_clicked(self) -> None:
        genre = self._current_genre()
        if genre is None:
            return
        anchor = self._anchor_path_for(genre)
        if anchor.is_file():
            anchor.unlink()
        self._preview_path = None
        self._refresh_genre_list()
        self._update_status(genre, has_anchor=False)
        self._replay_btn.setEnabled(False)
        self._use_btn.setEnabled(False)
        self._reset_btn.setEnabled(False)

    # ── Playback ──────────────────────────────────────────────────────────────

    def _play_wav(self, path: Path) -> None:
        try:
            import sounddevice as sd
            import soundfile as sf
            data, sr = sf.read(str(path), dtype="float32")
            sd.play(data, sr)
            self._watcher = _PlaybackWatcher(sd)
            self._watcher.finished.connect(self._on_playback_finished)
            self._watcher.start()
        except Exception as exc:
            self._log_lbl.setText(f"Playback error: {exc}")

    @pyqtSlot()
    def _on_playback_finished(self) -> None:
        self._log_lbl.hide()
        self._log_lbl.setText("")
        self._log_lbl.show()

    # ── Language selection ────────────────────────────────────────────────────

    @pyqtSlot(int)
    def _on_language_changed(self, index: int) -> None:
        self._language = self._lang_combo.itemData(index) or "en"
        # Refresh dots (existing anchors are language-specific)
        self._refresh_genre_list()
        # Update status and buttons for the current genre
        genre = self._current_genre()
        if genre:
            has_anchor = self._anchor_path_for(genre).is_file()
            self._update_status(genre, has_anchor)
            self._replay_btn.setEnabled(False)
            self._use_btn.setEnabled(False)
            self._reset_btn.setEnabled(has_anchor)
    
            self._preview_path = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _anchor_path_for(self, genre: str) -> Path:
        lang = self._language or "en"
        path = VOICE_ANCHORS_DIR / f"anchor_{genre}_{lang}.wav"
        if not path.is_file() and lang == "en":
            # Legacy: anchors generated before language suffixes were introduced
            legacy = VOICE_ANCHORS_DIR / f"anchor_{genre}.wav"
            if legacy.is_file():
                return legacy
        return path

    def _current_genre(self) -> str | None:
        row = self._genre_list.currentRow()
        return _GENRES[row] if 0 <= row < len(_GENRES) else None

    def _refresh_genre_list(self) -> None:
        current_row = self._genre_list.currentRow()
        self._genre_list.blockSignals(True)
        self._genre_list.clear()
        for genre in _GENRES:
            has = self._anchor_path_for(genre).is_file()
            item = QListWidgetItem(f"{'●' if has else '○'}  {genre.capitalize()}")
            item.setForeground(QColor("#22c55e" if has else "#475569"))
            self._genre_list.addItem(item)
        self._genre_list.blockSignals(False)
        self._genre_list.setCurrentRow(current_row)

    def _update_status(
        self,
        genre: str,
        has_anchor: bool,
        confirmed: bool = False,
    ) -> None:
        if has_anchor:
            self._status_dot_lbl.setText("●")
            self._status_dot_lbl.setStyleSheet("color: #22c55e; font-size: 14px;")
            msg = f"Voice saved for {genre}." if confirmed else f"Voice saved for {genre}."
            self._status_text_lbl.setText(msg)
        else:
            self._status_dot_lbl.setText("○")
            self._status_dot_lbl.setStyleSheet("color: #2d3748; font-size: 14px;")
            self._status_text_lbl.setText("No saved voice — click Generate to create one.")


class _PlaybackWatcher(QThread):
    """Waits for sounddevice playback to finish, then emits finished."""

    finished = pyqtSignal()

    def __init__(self, sd_module) -> None:
        super().__init__()
        self._sd = sd_module

    def run(self) -> None:
        self._sd.wait()
        self.finished.emit()
