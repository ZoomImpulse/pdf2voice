"""QThread-based pipeline workers for pdf2voice."""
from __future__ import annotations

import threading

from PyQt6.QtCore import QThread, pyqtSignal


class PipelineWorker(QThread):
    # ── Log signals ────────────────────────────────────────────────────
    log_info    = pyqtSignal(str)
    log_success = pyqtSignal(str)
    log_warn    = pyqtSignal(str)
    log_error   = pyqtSignal(str)

    # ── Stage signals ──────────────────────────────────────────────────
    stage_progress = pyqtSignal(int, int, int)   # stage, value, maximum
    stage_running  = pyqtSignal(int)
    stage_done     = pyqtSignal(int)
    stage_error    = pyqtSignal(int)

    # ── Chapter signals ────────────────────────────────────────────────
    book_ready      = pyqtSignal(object)          # StructuredBook
    chapters_ready  = pyqtSignal(list)            # list[tuple[int, str]]
    chapters_streaming = pyqtSignal(list)         # list[Chapter] — progressive updates during structuring
    chapter_running = pyqtSignal(int)
    chapter_done    = pyqtSignal(int)

    # ── Control signals ────────────────────────────────────────────────
    awaiting_confirm = pyqtSignal()
    all_done         = pyqtSignal(list, object)   # output_paths, final_path | None
    failed           = pyqtSignal(str)

    def __init__(
        self,
        pdf_path: str,
        gender: str,
        force_fresh: bool = False,
        force_resume: bool = False,
    ) -> None:
        super().__init__()
        self.pdf_path     = pdf_path
        self.gender       = gender
        self._force_fresh  = force_fresh
        self._force_resume = force_resume

        self._confirm_event = threading.Event()
        self._cancelled     = False
        self._paused        = False
        self._current_stage = 0

    # ── Public control interface ───────────────────────────────────────

    def confirm(self) -> None:
        self._confirm_event.set()

    def cancel(self) -> None:
        self._cancelled = True
        self._confirm_event.set()          # unblock any waiting confirm

    def toggle_pause(self) -> bool:
        """Toggle pause state; returns True when now paused."""
        self._paused = not self._paused
        return self._paused

    # ── QThread entry point ────────────────────────────────────────────

    def run(self) -> None:
        try:
            self._run_pipeline()
        except _Cancelled:
            pass
        except Exception as exc:
            self.failed.emit(str(exc))

    # ── Helpers ────────────────────────────────────────────────────────

    def _check_cancel(self) -> None:
        if self._cancelled:
            raise _Cancelled
        while self._paused and not self._cancelled:
            self.msleep(150)
        if self._cancelled:
            raise _Cancelled

    # ── Pipeline ───────────────────────────────────────────────────────

    def _run_pipeline(self) -> None:
        from src.pipeline.extractor import count_pages, extract_pdf
        from src.pipeline.session import (
            BookSession, book_from_session, compute_pdf_hash, create_session,
        )
        from src.pipeline.structurer import structure_content
        from src.pipeline.tts_engine import generate_audiobook
        from src.config import LLM_MODEL, OUTPUT_DIR

        pdf_path = self.pdf_path
        gender   = self.gender

        # ── Hash the PDF ───────────────────────────────────────────────
        self.log_info.emit("Scanning PDF fingerprint …")
        pdf_hash = compute_pdf_hash(pdf_path)

        # ── Check for an existing session ──────────────────────────────
        existing = BookSession.load(pdf_hash)

        if self._force_fresh and existing:
            self.log_info.emit("Starting fresh — previous session discarded.")
            existing.delete()
            existing = None

        resuming = False
        if existing is not None and not existing.is_complete:
            if self._force_resume:
                resuming = True
                if existing.gender != gender:
                    self.log_warn.emit(
                        f"Resuming with gender '{gender}' "
                        f"(session was recorded as '{existing.gender}')."
                    )
            elif existing.gender == gender:
                resuming = True
            # else: gender mismatch without force flags — handled by dialog in app.py
        elif existing and existing.is_complete:
            self.log_info.emit("Session already complete — starting fresh.")
            existing.delete()
            existing = None

        session = None
        book    = None

        if resuming and existing:
            # ── RESUME path ────────────────────────────────────────────
            session = existing
            book    = book_from_session(session)
            done    = session.completed_count
            total   = len(session.chapters)
            self.log_info.emit(
                f'Resuming "{session.title}" — {done}/{total} chapters already done.'
            )
            self.stage_done.emit(0)
            self.stage_done.emit(1)
            self.book_ready.emit(book)
            self.chapters_ready.emit([(ch.index, ch.title) for ch in book.chapters])
            for ch in session.chapters:
                if ch.done:
                    self.chapter_done.emit(ch.index)
            self.log_info.emit(
                "Review the chapter list and preview, then click "
                "Confirm & Generate to continue."
            )
            self.awaiting_confirm.emit()
            self._confirm_event.wait()
            self._check_cancel()

        else:
            # ── FRESH RUN ──────────────────────────────────────────────

            # Stage 0: PDF Extraction
            self._current_stage = 0
            self.stage_running.emit(0)
            self.log_info.emit(f"Extracting PDF: {pdf_path}")

            total_pages = count_pages(pdf_path)
            self.log_info.emit(f"Found: {total_pages} pages")

            def _extract_cb(cur: int, tot: int) -> None:
                self.stage_progress.emit(0, cur, max(tot, 1))

            markdown = extract_pdf(pdf_path, _extract_cb)
            self.stage_done.emit(0)
            self.log_success.emit(f"PDF extracted ({len(markdown):,} characters)")
            self._check_cancel()

            # Stage 1: LLM Structuring
            self._current_stage = 1
            self.stage_running.emit(1)
            self.log_info.emit(f"AI structuring content via {LLM_MODEL} …")

            def _llm_log(msg: str) -> None:
                self.log_info.emit(msg)

            def _chapters_streaming(chapters: list) -> None:
                """Called when new chapters become available during structuring."""
                # Emit signal for UI to display chapters progressively
                for ch in chapters:
                    self.chapters_streaming.emit([(ch.index, ch.title)])

            def _check_structure_pause() -> None:
                """Check for pause during structuring."""
                while self._paused and not self._cancelled:
                    self.msleep(150)
                if self._cancelled:
                    raise _Cancelled

            def _llm_progress(token_count: int) -> None:
                """Emit indeterminate progress for the progress bar while LLM streams."""
                self.stage_progress.emit(1, token_count, 0)

            book = structure_content(
                markdown,
                _llm_log,
                chapters_cb=_chapters_streaming,
                check_pause=_check_structure_pause,
                progress_cb=_llm_progress,
            )
            self.stage_done.emit(1)
            self.log_success.emit(
                f'Structured: "{book.title}" — '
                f"{len(book.chapters)} chapters, {book.total_chunks} chunks"
            )
            if book.genre:
                self.log_info.emit(f"Genre: {book.genre}")
            self.log_info.emit(f"Voice: {book.voice_instruct}")

            self.book_ready.emit(book)
            self.chapters_ready.emit([(ch.index, ch.title) for ch in book.chapters])
            self._check_cancel()

            session = create_session(book, pdf_hash, pdf_path, gender)
            session.save()
            self.log_info.emit("Session saved — generation can be resumed if interrupted.")
            self.log_info.emit(
                "Review the chapter previews, then click "
                "Confirm & Generate to start TTS generation."
            )
            self.awaiting_confirm.emit()
            self._confirm_event.wait()
            self._check_cancel()

        # ── Stage 2: Voice Anchor ──────────────────────────────────────
        self._current_stage = 2
        self.stage_running.emit(2)
        gender_label = "Female" if gender == "female" else "Male"
        self.log_info.emit(f"Voice Anchor: generating reference ({gender_label}) …")

        _anchor_stage_done = False

        def _anchor_cb(pct: float) -> None:
            nonlocal _anchor_stage_done
            self.stage_progress.emit(2, int(pct), 100)
            if pct >= 100.0 and not _anchor_stage_done:
                _anchor_stage_done = True
                self.stage_done.emit(2)
                self._current_stage = 3
                self.stage_running.emit(3)

        def _tts_log(msg: str) -> None:
            self.log_info.emit(msg)

        def _content_cb(ch_idx: int, g_chunk: int, tot_ch: int, tot_chunks: int) -> None:
            pct = int((g_chunk / max(tot_chunks, 1)) * 100)
            self.stage_progress.emit(3, pct, 100)
            self.chapter_running.emit(ch_idx + 1)

        def _is_cancelled() -> bool:
            return self._cancelled

        output_paths, final_path = generate_audiobook(
            book=book,
            gender=gender,
            log_cb=_tts_log,
            anchor_cb=_anchor_cb,
            content_cb=_content_cb,
            cancelled=_is_cancelled,
            session=session,
        )

        for ch in book.chapters:
            self.chapter_done.emit(ch.index)
        self.stage_done.emit(3)

        self.log_success.emit(
            f"Done! {len(output_paths)} chapter file(s) in {OUTPUT_DIR}"
        )
        for p in output_paths:
            self.log_info.emit(f"  Chapter → {p.name}")
        if final_path and len(output_paths) > 1:
            self.log_success.emit(f"  Complete → {final_path.name}")

        self.all_done.emit(output_paths, final_path)


class _Cancelled(Exception):
    """Internal sentinel raised when the pipeline is cancelled."""
