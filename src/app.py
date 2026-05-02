"""pdf2voice — Main PyQt6 application window."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.config import LLM_MODEL, OUTPUT_DIR, TTS_BASE_MODEL, TTS_DESIGN_MODEL, TTS_GENDER
from src.styles import DARK_STYLESHEET
from src.widgets.chapter_list import ChapterListPanel
from src.widgets.log_panel import LogPanel
from src.widgets.pipeline_panel import PipelinePanel
from src.widgets.preview_panel import PreviewPanel
from src.workers import PipelineWorker


class Pdf2VoiceApp(QMainWindow):
    def __init__(self, pdf_path: str | None = None) -> None:
        super().__init__()
        self._initial_path = pdf_path or ""
        self._worker: PipelineWorker | None = None
        self._book = None

        self.setWindowTitle("pdf2voice — PDF \u2192 Audiobook")
        self.resize(1400, 860)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        self._build_ui()

    # \u2500\u2500 UI construction \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._make_header())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._make_left_panel())
        splitter.addWidget(self._make_center_panel())
        splitter.addWidget(self._make_right_panel())
        splitter.setSizes([280, 720, 320])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        root_layout.addWidget(splitter, stretch=1)

        root_layout.addWidget(self._make_footer())

    # \u2500\u2500 Header \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _make_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("header-bar")
        frame.setFixedHeight(52)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("\U0001f3b5  pdf2voice")
        title.setObjectName("app-title")
        layout.addWidget(title)
        layout.addStretch()

        self._open_output_btn = QPushButton("\U0001f4c2  Open Output")
        self._open_output_btn.setObjectName("header-btn")
        self._open_output_btn.clicked.connect(self._open_output)
        layout.addWidget(self._open_output_btn)

        return frame

    # \u2500\u2500 Left panel \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _make_left_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("left-panel")
        frame.setFixedWidth(280)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # PDF Input
        input_box = QGroupBox("PDF File")
        il = QVBoxLayout(input_box)
        il.setSpacing(6)

        self._path_edit = QLineEdit(self._initial_path)
        self._path_edit.setObjectName("path-edit")
        self._path_edit.setPlaceholderText("Path to PDF file \u2026")
        il.addWidget(self._path_edit)

        self._browse_btn = QPushButton("Browse \u2026")
        self._browse_btn.setObjectName("browse-btn")
        self._browse_btn.clicked.connect(self._browse_pdf)
        il.addWidget(self._browse_btn)

        layout.addWidget(input_box)

        # Voice selector
        voice_box = QGroupBox("Voice")
        vl = QVBoxLayout(voice_box)
        vl.setSpacing(4)

        self._btn_female = QRadioButton("\u2640  Female")
        self._btn_male   = QRadioButton("\u2642  Male")
        self._gender_grp = QButtonGroup(self)
        self._gender_grp.addButton(self._btn_female)
        self._gender_grp.addButton(self._btn_male)
        (self._btn_female if TTS_GENDER == "female" else self._btn_male).setChecked(True)
        vl.addWidget(self._btn_female)
        vl.addWidget(self._btn_male)

        layout.addWidget(voice_box)

        # Settings display
        settings_box = QGroupBox("Settings")
        sl = QVBoxLayout(settings_box)
        sl.setSpacing(4)

        design_short = TTS_DESIGN_MODEL.split("/")[-1].replace("Qwen3-TTS-12Hz-", "")
        base_short   = TTS_BASE_MODEL.split("/")[-1].replace("Qwen3-TTS-12Hz-", "")
        for key, val in [
            ("LLM",    LLM_MODEL),
            ("Anchor", design_short),
            ("Base",   base_short),
            ("Output", str(OUTPUT_DIR)),
        ]:
            row = QHBoxLayout()
            row.setSpacing(4)
            k = QLabel(key + ":")
            k.setObjectName("settings-key")
            k.setFixedWidth(52)
            v = QLabel(val)
            v.setObjectName("settings-val")
            v.setWordWrap(True)
            row.addWidget(k)
            row.addWidget(v, stretch=1)
            sl.addLayout(row)

        layout.addWidget(settings_box)
        layout.addStretch()

        return frame

    # \u2500\u2500 Center panel \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _make_center_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("center-panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(10)

        self._pipeline_panel = PipelinePanel()
        layout.addWidget(self._pipeline_panel)

        # Inline confirmation banner — hidden until AI structuring finishes
        self._confirm_bar = self._make_confirm_bar()
        self._confirm_bar.setVisible(False)
        layout.addWidget(self._confirm_bar)

        self._chapter_list = ChapterListPanel()
        self._chapter_list.chapter_selected.connect(self._on_chapter_selected)
        layout.addWidget(self._chapter_list, stretch=1)

        return frame

    def _make_confirm_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("confirm-bar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(14)

        icon = QLabel("ℹ️")
        icon.setObjectName("confirm-bar-icon")
        layout.addWidget(icon)

        self._confirm_msg = QLabel(
            "AI structuring complete — review the chapters, then generate audio."
        )
        self._confirm_msg.setObjectName("confirm-bar-msg")
        self._confirm_msg.setWordWrap(True)
        layout.addWidget(self._confirm_msg, stretch=1)

        btn = QPushButton("▶▶  Generate Audio")
        btn.setObjectName("btn-generate")
        btn.setFixedHeight(34)
        btn.clicked.connect(self._confirm_tts)
        layout.addWidget(btn)

        return bar

    # \u2500\u2500 Right panel \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _make_right_panel(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        self._preview_panel = PreviewPanel()
        splitter.addWidget(self._preview_panel)

        self._log_panel = LogPanel()
        splitter.addWidget(self._log_panel)

        splitter.setSizes([420, 280])
        return splitter

    # \u2500\u2500 Footer \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _make_footer(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("footer-bar")
        frame.setFixedHeight(56)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        self._start_btn  = QPushButton("\u25b6  Start")
        self._pause_btn  = QPushButton("\u23f8  Pause")
        self._cancel_btn = QPushButton("\u2715  Cancel")

        self._start_btn.setObjectName("btn-start")
        self._pause_btn.setObjectName("btn-pause")
        self._cancel_btn.setObjectName("btn-cancel")

        self._pause_btn.setEnabled(False)
        self._cancel_btn.setEnabled(False)

        for btn in (self._start_btn, self._pause_btn, self._cancel_btn):
            btn.setFixedHeight(36)
            layout.addWidget(btn)

        layout.addStretch()

        self._status_lbl = QLabel("Ready")
        self._status_lbl.setObjectName("status-label")
        layout.addWidget(self._status_lbl)

        self._start_btn.clicked.connect(self._start_pipeline)
        self._pause_btn.clicked.connect(self._toggle_pause)
        self._cancel_btn.clicked.connect(self._cancel_pipeline)

        return frame

    # \u2500\u2500 Actions \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _browse_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF files (*.pdf);;All files (*.*)"
        )
        if path:
            self._path_edit.setText(path)

    def _open_output(self) -> None:
        path = str(OUTPUT_DIR.resolve())
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    @pyqtSlot(int, str)
    def _on_chapter_selected(self, index: int, title: str) -> None:
        if self._book is None:
            return
        chapter = next(
            (ch for ch in self._book.chapters if ch.index == index), None
        )
        if chapter is None:
            return
        from src.pipeline.tts_engine import _chapter_title_text
        announcement = _chapter_title_text(
            chapter.index, chapter.title, self._book.subdivision_type
        )
        self._preview_panel.show_chapter(
            index=chapter.index,
            title=chapter.title,
            chunks=chapter.chunks,
            subdivision_type=self._book.subdivision_type,
            title_announcement=announcement,
        )

    # \u2500\u2500 Pipeline control \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _get_gender(self) -> str:
        return "female" if self._btn_female.isChecked() else "male"

    def _start_pipeline(self) -> None:
        pdf_path = self._path_edit.text().strip()
        if not pdf_path:
            self._log_panel.error("Please select a PDF file first.")
            return
        if not Path(pdf_path).is_file():
            self._log_panel.error(f"File not found: {pdf_path}")
            return

        force_fresh  = False
        force_resume = False

        # Check for an existing incomplete session before spawning the worker
        try:
            from src.pipeline.session import BookSession, compute_pdf_hash
            pdf_hash = compute_pdf_hash(pdf_path)
            existing = BookSession.load(pdf_hash)
            if existing is not None and not existing.is_complete:
                done  = existing.completed_count
                total = len(existing.chapters)
                gender_note = (
                    f"  (recorded as {existing.gender}, currently set to {self._get_gender()})"
                    if existing.gender != self._get_gender() else ""
                )
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Existing Session")
                dlg.setText(
                    f'<b>{existing.title or "Untitled book"}</b>'
                    f"<br><br>A previous session was found for this PDF."
                    f"<br>{done} of {total} chapters already completed{gender_note}."
                    f"<br><br>Would you like to <b>resume</b> or <b>start fresh</b>?"
                )
                dlg.setIcon(QMessageBox.Icon.Question)
                btn_resume = dlg.addButton("Resume", QMessageBox.ButtonRole.AcceptRole)
                btn_fresh  = dlg.addButton("Start Fresh", QMessageBox.ButtonRole.DestructiveRole)
                dlg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                dlg.exec()
                clicked = dlg.clickedButton()
                if clicked is btn_resume:
                    force_resume = True
                elif clicked is btn_fresh:
                    force_fresh = True
                else:
                    return   # user cancelled
        except Exception:
            pass  # session check is best-effort; proceed normally if it fails

        self._book = None
        self._pipeline_panel.reset_all()
        self._chapter_list.clear()
        self._log_panel.clear()
        self._preview_panel.show_placeholder()
        self._set_controls("running")
        self._status_lbl.setText("Running \u2026")

        self._worker = PipelineWorker(
            pdf_path, self._get_gender(),
            force_fresh=force_fresh, force_resume=force_resume,
        )
        self._wire_worker(self._worker)
        self._worker.start()

    def _wire_worker(self, w: PipelineWorker) -> None:
        w.log_info.connect(self._log_panel.info)
        w.log_success.connect(self._log_panel.success)
        w.log_warn.connect(self._log_panel.warn)
        w.log_error.connect(self._log_panel.error)

        w.stage_progress.connect(self._on_stage_progress)
        w.stage_running.connect(self._pipeline_panel.mark_running)
        w.stage_done.connect(self._pipeline_panel.mark_done)
        w.stage_error.connect(self._pipeline_panel.mark_error)

        w.book_ready.connect(self._on_book_ready)
        w.chapters_ready.connect(self._on_chapters_ready)
        w.chapters_streaming.connect(self._on_chapters_streaming)
        w.chapter_running.connect(self._chapter_list.set_running)
        w.chapter_done.connect(self._chapter_list.set_done)

        w.awaiting_confirm.connect(self._on_awaiting_confirm)
        w.all_done.connect(self._on_all_done)
        w.failed.connect(self._on_failed)
        w.finished.connect(self._on_worker_finished)

    @pyqtSlot(int, int, int)
    def _on_stage_progress(self, stage: int, value: int, maximum: int) -> None:
        self._pipeline_panel.set_stage_progress(stage, value, maximum)

    @pyqtSlot(object)
    def _on_book_ready(self, book) -> None:
        self._book = book

    @pyqtSlot(list)
    def _on_chapters_ready(self, chapters: list) -> None:
        self._chapter_list.load_chapters(chapters)
        self._preview_panel.show_placeholder()

    @pyqtSlot(list)
    def _on_chapters_streaming(self, chapters: list) -> None:
        """Handle progressively streamed chapters during structuring."""
        self._chapter_list.add_chapters(chapters)

    @pyqtSlot()
    def _on_awaiting_confirm(self) -> None:
        self._confirm_bar.setVisible(True)
        self._set_controls("awaiting")
        self._status_lbl.setText("Review chapters \u2026")

    @pyqtSlot(list, object)
    def _on_all_done(self, output_paths: list, final_path) -> None:
        self._status_lbl.setText(f"Done \u2014 {len(output_paths)} chapter(s)")

    @pyqtSlot(str)
    def _on_failed(self, error: str) -> None:
        self._log_panel.error(f"Error: {error}")
        if self._worker:
            self._pipeline_panel.mark_error(self._worker._current_stage)

    @pyqtSlot()
    def _on_worker_finished(self) -> None:
        self._set_controls("idle")

    def _confirm_tts(self) -> None:
        self._confirm_bar.setVisible(False)
        if self._worker:
            self._worker.confirm()
        self._set_controls("running")
        self._log_panel.info("Confirmed \u2014 starting TTS generation \u2026")
        self._status_lbl.setText("Generating \u2026")

    def _toggle_pause(self) -> None:
        if self._worker:
            paused = self._worker.toggle_pause()
            self._pause_btn.setText("\u25b6  Resume" if paused else "\u23f8  Pause")
            self._status_lbl.setText("Paused" if paused else "Running \u2026")

    def _cancel_pipeline(self) -> None:
        self._confirm_bar.setVisible(False)
        if self._worker:
            self._worker.cancel()
        self._log_panel.error("Pipeline cancelled.")
        self._set_controls("idle")
        self._status_lbl.setText("Cancelled")

    # \u2500\u2500 Helper \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _set_controls(self, state: str) -> None:
        """state: 'idle' | 'awaiting' | 'running'"""
        is_idle    = state == "idle"
        is_running = state == "running"
        self._start_btn.setEnabled(is_idle)
        self._pause_btn.setEnabled(is_running)
        self._cancel_btn.setEnabled(not is_idle)
        if is_idle:
            self._status_lbl.setText("Ready")
