"""pdf2voice — Main PyQt6 application window (Concept 3: vertical card layout)."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.config import GENRE_PROMPTS, OUTPUT_DIR, VOICE_ANCHORS_DIR
from src.styles import DARK_STYLESHEET
from src.widgets.chapter_section import ChapterSection
from src.widgets.info_bar import InfoBar
from src.widgets.log_panel import LogPanel
from src.widgets.pipeline_section import PipelineSection
from src.widgets.settings_dialog import SettingsDialog
from src.widgets.voice_designer_dialog import VoiceDesignerDialog
from src.workers import PipelineWorker, RegenerationWorker


class Pdf2VoiceApp(QMainWindow):
    def __init__(self, pdf_path: str | None = None) -> None:
        super().__init__()
        self._initial_path = pdf_path or ""
        self._worker: PipelineWorker | None = None
        self._regen_worker: RegenerationWorker | None = None
        self._book = None
        self._session = None
        self._app_state = "idle"   # "idle"|"running"|"awaiting"|"complete"|"regenerating"

        self.setWindowTitle("pdf2voice — PDF → Audiobook")
        self.resize(1000, 860)
        self.setMinimumSize(700, 500)
        self.setStyleSheet(DARK_STYLESHEET)

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._make_header())
        root_layout.addWidget(self._make_scroll_body(), stretch=1)
        root_layout.addWidget(self._make_footer())

        # Wire persistent signals
        self._chapter_section.chapter_edit_saved.connect(self._on_chapter_edit_saved)
        self._chapter_section.chapter_regen_requested.connect(self._on_chapter_regen_requested)
        self._chapter_section.chapter_selected.connect(self._on_chapter_selected)
        self._chapter_section.chapter_delete_requested.connect(self._on_chapter_delete_requested)
        self._info_bar.pdf_selected.connect(self._on_pdf_selected)

        # Check for incomplete sessions after the window is shown
        if not self._initial_path:
            QTimer.singleShot(200, self._check_startup_sessions)

    # ── Header ────────────────────────────────────────────────────────────────

    def _make_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("header-bar")
        frame.setFixedHeight(52)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("🎵  pdf2voice")
        title.setObjectName("app-title")
        layout.addWidget(title)
        layout.addStretch()

        self._open_output_btn = QPushButton("📂  Open Output")
        self._open_output_btn.setObjectName("header-btn")
        self._open_output_btn.clicked.connect(self._open_output)
        layout.addWidget(self._open_output_btn)

        self._voice_designer_btn = QPushButton("🎙  Voices")
        self._voice_designer_btn.setObjectName("header-btn")
        self._voice_designer_btn.clicked.connect(self._open_voice_designer)
        layout.addWidget(self._voice_designer_btn)

        self._settings_btn = QPushButton("⚙️  Settings")
        self._settings_btn.setObjectName("header-btn")
        self._settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(self._settings_btn)

        return frame

    # ── Scrollable body ───────────────────────────────────────────────────────

    def _make_scroll_body(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body.setObjectName("scroll-body")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── Info cards row ────────────────────────────────────────────
        self._info_bar = InfoBar(self._initial_path)
        layout.addWidget(self._info_bar)

        # ── Pipeline section ──────────────────────────────────────────
        self._pipeline_panel = PipelineSection()
        layout.addWidget(self._pipeline_panel)

        # ── Confirmation banner (hidden until structuring finishes) ───
        self._confirm_bar = self._make_confirm_bar()
        self._confirm_bar.setVisible(False)
        layout.addWidget(self._confirm_bar)

        # ── Chapter review section ────────────────────────────────────
        self._chapter_section = ChapterSection()
        layout.addWidget(self._chapter_section)

        # ── Activity log ──────────────────────────────────────────────
        self._log_panel = LogPanel()
        self._log_panel.setMinimumHeight(180)
        layout.addWidget(self._log_panel)

        layout.addStretch()
        scroll.setWidget(body)
        return scroll

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

        genre_lbl = QLabel("Genre:")
        genre_lbl.setObjectName("confirm-bar-msg")
        layout.addWidget(genre_lbl)

        self._genre_combo = QComboBox()
        self._genre_combo.setObjectName("genre-combo")
        self._genre_combo.addItems(list(GENRE_PROMPTS.keys()))
        self._genre_combo.setFixedHeight(30)
        self._genre_combo.setMinimumWidth(120)
        self._genre_combo.currentTextChanged.connect(self._on_genre_changed)
        layout.addWidget(self._genre_combo)

        btn = QPushButton("▶▶  Generate Audio")
        btn.setObjectName("btn-generate")
        btn.setFixedHeight(34)
        btn.clicked.connect(self._confirm_tts)
        layout.addWidget(btn)

        return bar

    # ── Footer ────────────────────────────────────────────────────────────────

    def _make_footer(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("footer-bar")
        frame.setFixedHeight(56)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        self._start_btn  = QPushButton("Start")
        self._pause_btn  = QPushButton("Pause")
        self._cancel_btn = QPushButton("Cancel")

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

    # ── Actions ───────────────────────────────────────────────────────────────


    def _open_output(self) -> None:
        path = str(OUTPUT_DIR.resolve())
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        dlg.exec()
        self._chapter_section.refresh_all_expanded()

    def _open_voice_designer(self) -> None:
        dlg = VoiceDesignerDialog(parent=self)
        dlg.exec()

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
        self._chapter_section.show_chapter(
            index=chapter.index,
            title=chapter.title,
            chunks=chapter.chunks,
            subdivision_type=self._book.subdivision_type,
            title_announcement=announcement,
        )

    # ── Chapter text editing ──────────────────────────────────────────────────

    @pyqtSlot(int, str)
    def _on_chapter_edit_saved(self, chapter_index: int, raw_text: str) -> None:
        if self._book is None:
            return
        from src.pipeline.preprocessor import chunk_text as pp_chunk
        from src.pipeline.preprocessor import SILENCE_PARA_S, SILENCE_CHUNK_S

        new_chunks: list[str] = []
        new_pauses: list[float] = []
        for para in re.split(r"\n{2,}", raw_text):
            para = para.strip()
            if not para:
                continue
            para_chunks = pp_chunk(para)
            for i, chunk in enumerate(para_chunks):
                new_chunks.append(chunk)
                new_pauses.append(
                    SILENCE_PARA_S if i == len(para_chunks) - 1 else SILENCE_CHUNK_S
                )

        if not new_chunks:
            self._log_panel.warn(f"Chapter {chapter_index}: empty text after editing, ignored.")
            return

        # Update StructuredBook in memory
        chapter = next(
            (ch for ch in self._book.chapters if ch.index == chapter_index), None
        )
        if chapter is None:
            return
        chapter.chunks       = new_chunks
        chapter.chunk_pauses = new_pauses

        # Update session and persist
        if self._session:
            self._session.update_chapter_text(chapter_index, new_chunks, new_pauses)
            self._session.save()

        # Reset chapter card to pending
        self._chapter_section.set_pending(chapter_index)

        # Refresh the expanded preview with updated chunks
        from src.pipeline.tts_engine import _chapter_title_text
        announcement = _chapter_title_text(
            chapter.index, chapter.title, self._book.subdivision_type
        )
        self._chapter_section.show_chapter(
            index=chapter.index,
            title=chapter.title,
            chunks=chapter.chunks,
            subdivision_type=self._book.subdivision_type,
            title_announcement=announcement,
        )

        self._log_panel.success(
            f"Chapter {chapter_index} re-chunked: "
            f"{len(new_chunks)} chunks, {sum(len(c) for c in new_chunks):,} characters"
        )

    # ── Chapter deletion ──────────────────────────────────────────────────────

    @pyqtSlot(int)
    def _on_chapter_delete_requested(self, chapter_index: int) -> None:
        if self._book is None:
            return
        reply = QMessageBox.question(
            self,
            "Kapitel löschen",
            f"Kapitel {chapter_index} wirklich löschen?\nDiese Aktion kann nicht rückgängig gemacht werden.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._book.chapters = [ch for ch in self._book.chapters if ch.index != chapter_index]
        if self._session:
            self._session.delete_chapter(chapter_index)
            self._session.save()

        self._chapter_section.remove_chapter(chapter_index)
        self._log_panel.info(f"Kapitel {chapter_index} gelöscht.")

    # ── Chapter regeneration ──────────────────────────────────────────────────

    @pyqtSlot(int)
    def _on_chapter_regen_requested(self, chapter_index: int) -> None:
        if self._app_state != "complete":
            return
        if self._book is None or self._session is None:
            return

        if not self._session.anchor_available():
            QMessageBox.warning(
                self,
                "Voice Anchor Missing",
                "The voice anchor file is missing.\n"
                "Chapters can only be regenerated when the anchor still exists.",
            )
            return

        chapter = next(
            (ch for ch in self._book.chapters if ch.index == chapter_index), None
        )
        if chapter is None:
            return

        # Delete old WAV before regenerating
        ch_state = self._session.chapter_state(chapter_index)
        if ch_state and ch_state.output:
            old_path = Path(ch_state.output)
            old_path.unlink(missing_ok=True)

        self._app_state = "regenerating"
        self._chapter_section.set_regen_enabled_all(False)
        self._chapter_section.set_running(chapter_index)
        self._status_lbl.setText(f"Regenerating chapter {chapter_index} …")
        self._log_panel.info(f"Regenerating chapter {chapter_index}: {chapter.title}")

        self._regen_worker = RegenerationWorker(
            chapter_index=chapter_index,
            book=self._book,
            session=self._session,
            gender="",
        )
        self._regen_worker.log_info.connect(self._log_panel.info)
        self._regen_worker.log_success.connect(self._log_panel.success)
        self._regen_worker.log_warn.connect(self._log_panel.warn)
        self._regen_worker.log_error.connect(self._log_panel.error)
        self._regen_worker.chapter_running.connect(self._chapter_section.set_running)
        self._regen_worker.chapter_done.connect(self._chapter_section.set_done)
        self._regen_worker.chapter_error.connect(self._chapter_section.set_error)
        self._regen_worker.regen_done.connect(self._on_regen_done)
        self._regen_worker.finished.connect(self._on_regen_worker_finished)
        self._regen_worker.start()

    @pyqtSlot(int, object)
    def _on_regen_done(self, chapter_index: int, final_path) -> None:
        if final_path:
            self._log_panel.success(f"Audiobook updated → {Path(final_path).name}")
        self._status_lbl.setText(f"Chapter {chapter_index} regenerated")

    @pyqtSlot()
    def _on_regen_worker_finished(self) -> None:
        self._app_state = "complete"
        self._chapter_section.set_regen_enabled_all(True)
        self._regen_worker = None

    # ── Pipeline control ──────────────────────────────────────────────────────

    def _check_startup_sessions(self) -> None:
        """On startup, find incomplete sessions and offer to resume one."""
        try:
            from src.pipeline.session import list_incomplete
            sessions = list_incomplete()
        except Exception:
            return
        if not sessions:
            return

        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout as _QHBox, QListWidget, QListWidgetItem

        # Mutable list so the delete button can update it in-place
        session_list: list = list(sessions)

        dlg = QDialog(self)
        dlg.setWindowTitle("Resume Previous Session?")
        dlg.setMinimumWidth(500)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        lbl = QLabel(
            f"<b>{len(session_list)} incomplete session{'s' if len(session_list) > 1 else ''} found.</b>"
            "<br>Select one to resume, or close this dialog to start fresh."
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        list_widget = QListWidget()

        def _populate() -> None:
            list_widget.clear()
            for s in session_list:
                done     = s.completed_count
                total    = len(s.chapters)
                pdf_name = Path(s.pdf_path).name if s.pdf_path else "unknown"
                item = QListWidgetItem(
                    f"{s.title or pdf_name}  —  {done}/{total} chapters"
                )
                item.setData(Qt.ItemDataRole.UserRole, s)
                list_widget.addItem(item)
            if list_widget.count():
                list_widget.setCurrentRow(0)
            lbl.setText(
                f"<b>{len(session_list)} incomplete session{'s' if len(session_list) > 1 else ''} found.</b>"
                "<br>Select one to resume, or close this dialog to start fresh."
            )

        _populate()
        layout.addWidget(list_widget)

        # ── Button row ────────────────────────────────────────────────
        btn_row = _QHBox()
        btn_row.setSpacing(8)

        delete_btn = QPushButton("🗑  Delete Selected")
        delete_btn.setObjectName("btn-delete-session")

        def _delete_selected() -> None:
            item = list_widget.currentItem()
            if not item:
                return
            s = item.data(Qt.ItemDataRole.UserRole)
            if not s:
                return
            confirm = QMessageBox.question(
                dlg, "Delete Session",
                f"Delete the session for <b>{s.title or 'this book'}</b>?<br>"
                "Already-generated audio files will not be removed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            try:
                s.delete()
            except Exception:
                pass
            session_list.remove(s)
            _populate()
            if not session_list:
                dlg.reject()

        delete_btn.clicked.connect(_delete_selected)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("Resume Selected")
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        btn_row.addWidget(btn_box)
        layout.addLayout(btn_row)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selected = list_widget.currentItem()
        if not selected:
            return
        session = selected.data(Qt.ItemDataRole.UserRole)
        if not session:
            return

        pdf_path = session.pdf_path
        if not pdf_path or not Path(pdf_path).is_file():
            QMessageBox.warning(
                self, "File Not Found",
                f"The original PDF could not be found:\n{pdf_path}\n\nPlease use Browse to locate it."
            )
            return

        self._force_fresh  = False
        self._force_resume = True
        self._info_bar.set_pdf_path(pdf_path)

    def _on_pdf_selected(self, pdf_path: str) -> None:
        """Called immediately when the user picks a PDF via Browse.

        Checks for an existing incomplete session and prompts the user to
        resume or start fresh.  The choice is stored so _start_pipeline can
        use it without asking again.
        """
        self._force_fresh  = False
        self._force_resume = False
        try:
            from src.pipeline.session import BookSession, compute_pdf_hash
            pdf_hash = compute_pdf_hash(pdf_path)
            existing = BookSession.load(pdf_hash)
            if existing is not None and not existing.is_complete:
                done  = existing.completed_count
                total = len(existing.chapters)
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Existing Session")
                dlg.setText(
                    f'<b>{existing.title or "Untitled book"}</b>'
                    f"<br><br>A previous session was found for this PDF."
                    f"<br>{done} of {total} chapters already completed."
                    f"<br><br>Would you like to <b>resume</b> or <b>start fresh</b>?"
                )
                dlg.setIcon(QMessageBox.Icon.Question)
                btn_resume = dlg.addButton("Resume", QMessageBox.ButtonRole.AcceptRole)
                btn_fresh  = dlg.addButton("Start Fresh", QMessageBox.ButtonRole.DestructiveRole)
                dlg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                dlg.exec()
                clicked = dlg.clickedButton()
                if clicked is btn_resume:
                    self._force_resume = True
                elif clicked is btn_fresh:
                    self._force_fresh = True
                # Cancel: no flags set, user can still pick another file or start later
        except Exception:
            pass  # session check is best-effort

    def _start_pipeline(self) -> None:
        pdf_path = self._info_bar.get_pdf_path()
        if not pdf_path:
            self._log_panel.error("Please select a PDF file first.")
            return
        if not Path(pdf_path).is_file():
            self._log_panel.error(f"File not found: {pdf_path}")
            return
        force_fresh  = getattr(self, "_force_fresh",  False)
        force_resume = getattr(self, "_force_resume", False)

        self._book    = None
        self._session = None
        self._app_state = "running"
        self._pipeline_panel.reset_all()
        self._chapter_section.clear()
        self._log_panel.clear()
        self._chapter_section.set_edit_allowed(False)
        self._set_controls("running")
        self._status_lbl.setText("Running …")
        self._info_bar.set_controls_enabled(False)

        self._worker = PipelineWorker(
            pdf_path, "",
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
        w.chapter_adapted.connect(self._on_chapter_adapted)
        w.chapter_running.connect(self._chapter_section.set_running)
        w.chapter_done.connect(self._chapter_section.set_done)

        w.awaiting_confirm.connect(self._on_awaiting_confirm)
        w.all_done.connect(self._on_all_done)
        w.failed.connect(self._on_failed)
        w.finished.connect(self._on_worker_finished)
        w.stage_status.connect(self._pipeline_panel.set_status)
        w.chunk_step.connect(self._pipeline_panel.set_chunk_step)

    @pyqtSlot(int, int, int)
    def _on_stage_progress(self, stage: int, value: int, maximum: int) -> None:
        self._pipeline_panel.set_stage_progress(stage, value, maximum)

    @pyqtSlot(object)
    def _on_book_ready(self, book) -> None:
        self._book = book

    @pyqtSlot(list)
    def _on_chapters_ready(self, chapters: list) -> None:
        self._chapter_section.load_chapters(chapters)

    @pyqtSlot(list)
    def _on_chapters_streaming(self, chapters: list) -> None:
        self._chapter_section.add_chapters(chapters)

    @pyqtSlot(int, str)
    def _on_chapter_adapted(self, index: int, title: str) -> None:
        """Called after each chapter is adapted — adds it to the list progressively."""
        self._chapter_section.add_chapters([(index, title)])

    @pyqtSlot()
    def _on_awaiting_confirm(self) -> None:
        self._app_state = "awaiting"
        if self._book:
            self._genre_combo.blockSignals(True)
            idx = self._genre_combo.findText(self._book.genre)
            if idx >= 0:
                self._genre_combo.setCurrentIndex(idx)
            self._genre_combo.blockSignals(False)
        self._confirm_bar.setVisible(True)
        self._set_controls("awaiting")
        self._chapter_section.set_edit_allowed(True)
        self._status_lbl.setText("Review chapters …")

    def _on_genre_changed(self, genre: str) -> None:
        if not genre or self._book is None:
            return
        self._book.genre = genre
        if self._session:
            self._session.genre = genre
            self._session.save()
        self._log_panel.info(f"Genre geändert zu: {genre}")

    @pyqtSlot(list, object)
    def _on_all_done(self, output_paths: list, final_path) -> None:
        self._app_state = "complete"
        if self._worker:
            self._session = self._worker.get_session()
        self._chapter_section.set_edit_allowed(True)
        self._status_lbl.setText(f"Done — {len(output_paths)} chapter(s)")

    @pyqtSlot(str)
    def _on_failed(self, error: str) -> None:
        self._log_panel.error(f"Error: {error}")
        if self._worker:
            self._pipeline_panel.mark_error(self._worker._current_stage)

    @pyqtSlot()
    def _on_worker_finished(self) -> None:
        self._info_bar.set_controls_enabled(True)
        if self._app_state != "complete":
            self._set_controls("idle")
        else:
            self._start_btn.setEnabled(True)
            self._pause_btn.setEnabled(False)
            self._cancel_btn.setEnabled(False)

    def _confirm_tts(self) -> None:
        genre = getattr(self._book, "genre", "") if self._book else ""
        genre_anchor = VOICE_ANCHORS_DIR / f"anchor_{genre}.wav" if genre else None
        session = self._worker.get_session() if self._worker else None

        has_anchor = (
            (session is not None and session.anchor_available())
            or (genre_anchor is not None and genre_anchor.is_file())
        )

        if not has_anchor:
            self._log_panel.warn(
                f"No saved voice for genre '{genre or 'unknown'}' — "
                "please design one in the Voice Designer first."
            )
            dlg = VoiceDesignerDialog(initial_genre=genre, parent=self)
            dlg.exec()

            # Re-check after the dialog closes
            if genre_anchor is None or not genre_anchor.is_file():
                self._log_panel.warn("Voice not saved — save a voice to continue.")
                return

        self._confirm_bar.setVisible(False)
        self._chapter_section.set_edit_allowed(False)
        if self._worker:
            self._worker.confirm()
        self._app_state = "running"
        self._set_controls("running")
        self._log_panel.info("Confirmed — starting TTS generation …")
        self._status_lbl.setText("Generating …")

    def _toggle_pause(self) -> None:
        if self._worker:
            paused = self._worker.toggle_pause()
            self._pause_btn.setText("▶  Resume" if paused else "⏸  Pause")
            self._status_lbl.setText("Paused" if paused else "Running …")

    def _cancel_pipeline(self) -> None:
        reply = QMessageBox.question(
            self,
            "Cancel Pipeline",
            "Are you sure you want to cancel the current run?\n"
            "Progress up to the last completed chunk will be saved.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._confirm_bar.setVisible(False)
        if self._worker:
            self._worker.cancel()
        self._pipeline_panel.mark_cancelled()
        self._log_panel.error("Pipeline cancelled.")
        self._app_state = "idle"
        self._set_controls("idle")
        self._info_bar.set_controls_enabled(True)
        self._status_lbl.setText("Cancelled")

    # ── Helper ────────────────────────────────────────────────────────────────

    def _set_controls(self, state: str) -> None:
        """state: 'idle' | 'awaiting' | 'running'"""
        is_idle    = state == "idle"
        is_running = state == "running"
        self._start_btn.setEnabled(is_idle)
        self._pause_btn.setEnabled(is_running)
        self._cancel_btn.setEnabled(not is_idle)
        if is_idle:
            self._status_lbl.setText("Ready")
