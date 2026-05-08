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
    chapter_adapted = pyqtSignal(int, str)        # index, title — emitted after each adaptation
    chapter_running = pyqtSignal(int)
    chapter_done    = pyqtSignal(int)

    # ── Control signals ────────────────────────────────────────────────
    awaiting_confirm = pyqtSignal()
    all_done         = pyqtSignal(list, object)   # output_paths, final_path | None
    failed           = pyqtSignal(str)
    stage_status     = pyqtSignal(str)            # free-form status override (e.g. per-chapter adapt)
    chunk_step       = pyqtSignal(int, int)        # step, total_steps within current chunk
    paused           = pyqtSignal()               # emitted when thread actually enters the pause wait loop
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

        self._confirm_event    = threading.Event()
        self._cancelled        = False
        self._paused           = False
        self._is_paused_waiting = False
        self._current_stage    = 0

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
        if self._paused and not self._is_paused_waiting:
            self._is_paused_waiting = True
            self.paused.emit()
        while self._paused and not self._cancelled:
            self.msleep(150)
        if self._is_paused_waiting:
            self._is_paused_waiting = False
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
            self._session_ref = session   # expose early so get_session() works during await
            book    = book_from_session(session)
            done    = session.completed_count
            total   = len(session.chapters)
            self.log_info.emit(
                f'Resuming "{session.title}" — {done}/{total} chapters already done.'
            )
            self.stage_done.emit(0)
            self.book_ready.emit(book)
            self.chapters_ready.emit([(ch.index, ch.title) for ch in book.chapters])
            for ch in session.chapters:
                if ch.done:
                    self.chapter_done.emit(ch.index)

            # ── Re-run adaptation for any chapters not yet adapted ─────
            from src.config import (
                ADAPTATION_ENABLED, ADAPTATION_PROVIDER,
                OPENROUTER_API_KEY, OPENROUTER_MODEL, OLLAMA_URL,
            )
            if ADAPTATION_ENABLED:
                pending = [ch for ch in book.chapters if ch.adapted_text is None]
                if pending:
                    self._current_stage = 1
                    self.stage_running.emit(1)
                    from src.pipeline.adapter import adapt_chapter
                    from src.pipeline.preprocessor import (
                        chunk_text, SILENCE_PARA_S, SILENCE_CHUNK_S,
                    )
                    import re as _re
                    adapt_model = (
                        OPENROUTER_MODEL if ADAPTATION_PROVIDER == "openrouter"
                        else LLM_MODEL
                    )
                    provider_label = ADAPTATION_PROVIDER.capitalize()
                    self.log_info.emit(
                        f"Resuming adaptation — {len(pending)} chapter(s) remaining "
                        f"via {provider_label} ({adapt_model}) …"
                    )
                    for chapter in pending:
                        self._check_cancel()
                        while self._paused and not self._cancelled:
                            self.msleep(150)
                        self._check_cancel()
                        self.stage_status.emit(
                            f"Adapting {chapter.index}/{len(book.chapters)}: "
                            f"{chapter.title[:40]} …"
                        )
                        self.log_info.emit(
                            f"  Adapting chapter {chapter.index}: {chapter.title}"
                        )
                        try:
                            adapted = adapt_chapter(
                                title=chapter.title,
                                chunks=chapter.chunks,
                                provider=ADAPTATION_PROVIDER,
                                model=adapt_model,
                                api_key=OPENROUTER_API_KEY,
                                ollama_base_url=OLLAMA_URL,
                                log_cb=lambda msg: self.log_info.emit(msg),
                            )
                            new_chunks: list[str] = []
                            new_pauses: list[float] = []
                            for para in _re.split(r"\n{2,}", adapted):
                                para = para.strip()
                                if not para:
                                    continue
                                para_chunks = chunk_text(para)
                                for i, c in enumerate(para_chunks):
                                    new_chunks.append(c)
                                    new_pauses.append(
                                        SILENCE_PARA_S if i == len(para_chunks) - 1
                                        else SILENCE_CHUNK_S
                                    )
                            if new_chunks:
                                chapter.adapted_text = adapted
                                chapter.chunks = new_chunks
                                chapter.chunk_pauses = new_pauses
                                ch_state = session.chapter_state(chapter.index)
                                if ch_state:
                                    ch_state.adapted_text = adapted
                                    ch_state.chunks = new_chunks
                                    ch_state.chunk_pauses = new_pauses
                                self.chapter_adapted.emit(chapter.index, chapter.title)
                        except Exception as exc:
                            self.log_warn.emit(
                                f"  Adaptation failed for '{chapter.title}': {exc}"
                                " — using original text"
                            )
                            self.chapter_adapted.emit(chapter.index, chapter.title)
                        session.save()
                    self.log_success.emit("Audiobook adaptation complete.")

            self.stage_done.emit(1)
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
                while self._paused and not self._cancelled:
                    self.msleep(150)
                if self._cancelled:
                    raise _Cancelled
                self.stage_progress.emit(0, cur, tot)

            markdown = extract_pdf(pdf_path, _extract_cb)
            self.stage_done.emit(0)
            self.log_success.emit(f"PDF extracted ({len(markdown):,} characters)")
            self._check_cancel()

            # Stage 1: LLM Structuring
            self._current_stage = 1
            self.stage_running.emit(1)

            from src.config import (
                ADAPTATION_ENABLED, ADAPTATION_PROVIDER,
                OPENROUTER_API_KEY, OPENROUTER_MODEL, OLLAMA_URL,
            )

            struct_model = (
                OPENROUTER_MODEL if ADAPTATION_PROVIDER == "openrouter"
                else LLM_MODEL
            )
            provider_label = ADAPTATION_PROVIDER.capitalize()
            self.log_info.emit(f"AI structuring content via {provider_label} ({struct_model}) …")

            def _llm_log(msg: str) -> None:
                self.log_info.emit(msg)

            def _chapters_streaming(chapters: list) -> None:
                """Called when new chapters become available during structuring."""
                # Only stream to UI if adaptation is disabled — otherwise chapters
                # fly in one by one after adaptation via chapter_adapted signal.
                if not ADAPTATION_ENABLED:
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
                pdf_path=pdf_path,
                model=struct_model,
                provider=ADAPTATION_PROVIDER,
                api_key=OPENROUTER_API_KEY,
                ollama_base_url=OLLAMA_URL,
            )
            self.log_success.emit(
                f'Structured: "{book.title}" — '
                f"{len(book.chapters)} chapters, {book.total_chunks} chunks"
            )
            if book.genre:
                self.log_info.emit(f"Genre: {book.genre}")
            self.log_info.emit(f"Voice: {book.voice_instruct}")

            self.book_ready.emit(book)

            # ── Audiobook Adaptation ───────────────────────────────────
            from src.pipeline.adapter import adapt_chapter
            from src.pipeline.preprocessor import (
                chunk_text, SILENCE_PARA_S, SILENCE_CHUNK_S,
            )
            import re as _re

            # Create session now so adaptation progress can be persisted incrementally
            session = create_session(book, pdf_hash, pdf_path, gender)
            session.save()
            self._session_ref = session   # expose early so get_session() works during await
            self.log_info.emit("Session saved — generation can be resumed if interrupted.")

            if ADAPTATION_ENABLED:
                adapt_model = (
                    OPENROUTER_MODEL if ADAPTATION_PROVIDER == "openrouter"
                    else LLM_MODEL
                )
                provider_label = ADAPTATION_PROVIDER.capitalize()
                self.log_info.emit(
                    f"Adapting {len(book.chapters)} chapter(s) for audio "
                    f"via {provider_label} ({adapt_model}) …"
                )
                for chapter in book.chapters:
                    self._check_cancel()
                    # Honour pause between adaptation calls
                    while self._paused and not self._cancelled:
                        self.msleep(150)
                    self._check_cancel()
                    self.stage_status.emit(
                        f"Adapting {chapter.index}/{len(book.chapters)}: "
                        f"{chapter.title[:40]} …"
                    )
                    self.log_info.emit(
                        f"  Adapting chapter {chapter.index}: {chapter.title}"
                    )
                    try:
                        adapted = adapt_chapter(
                            title=chapter.title,
                            chunks=chapter.chunks,
                            provider=ADAPTATION_PROVIDER,
                            model=adapt_model,
                            api_key=OPENROUTER_API_KEY,
                            ollama_base_url=OLLAMA_URL,
                            log_cb=lambda msg: self.log_info.emit(msg),
                        )
                        # Re-chunk the adapted prose
                        new_chunks: list[str] = []
                        new_pauses: list[float] = []
                        for para in _re.split(r"\n{2,}", adapted):
                            para = para.strip()
                            if not para:
                                continue
                            para_chunks = chunk_text(para)
                            for i, c in enumerate(para_chunks):
                                new_chunks.append(c)
                                new_pauses.append(
                                    SILENCE_PARA_S if i == len(para_chunks) - 1
                                    else SILENCE_CHUNK_S
                                )
                        if new_chunks:
                            chapter.adapted_text = adapted
                            chapter.chunks = new_chunks
                            chapter.chunk_pauses = new_pauses
                            # Mirror adapted content into session and persist
                            ch_state = session.chapter_state(chapter.index)
                            if ch_state:
                                ch_state.adapted_text = adapted
                                ch_state.chunks = new_chunks
                                ch_state.chunk_pauses = new_pauses
                            self.chapter_adapted.emit(chapter.index, chapter.title)
                    except Exception as exc:
                        self.log_warn.emit(
                            f"  Adaptation failed for '{chapter.title}': {exc}"
                            " — using original text"
                        )
                        self.chapter_adapted.emit(chapter.index, chapter.title)
                    session.save()
                self.log_success.emit("Audiobook adaptation complete.")
            else:
                # No adaptation — emit all chapters at once
                self.chapters_ready.emit([(ch.index, ch.title) for ch in book.chapters])
            self._check_cancel()
            self.stage_done.emit(1)
            self.log_info.emit(
                "Review the chapter previews, then click "
                "Confirm & Generate to start TTS generation."
            )
            self.awaiting_confirm.emit()
            self._confirm_event.wait()
            self._check_cancel()

        # ── Stage 2: Generation (includes voice anchor loading) ────────
        self._current_stage = 2
        self.stage_running.emit(2)

        def _anchor_cb(pct: float) -> None:
            while self._paused and not self._cancelled:
                self.msleep(150)
            if self._cancelled:
                raise _Cancelled

        def _tts_log(msg: str) -> None:
            self.log_info.emit(msg)

        # Tracks which chunk is currently being synthesised so the step callback
        # can embed chapter/chunk context in the status label.
        _current_chunk_label: list[str] = ["Generating speech"]

        def _chunk_start_cb(ch_idx: int, ck_idx: int, n_chunks: int, tot_ch: int) -> None:
            label = f"Chapter {ch_idx + 1}/{tot_ch} — chunk {ck_idx + 1}/{n_chunks}"
            _current_chunk_label[0] = label
            self.stage_status.emit(label)

        def _chunk_step_cb(step: int, total: int) -> None:
            if total > 0:
                self.chunk_step.emit(step, total)
                pct = int((step / total) * 100)
                label = _current_chunk_label[0]
                eta_str = ""
                # Rough ETA based on steps remaining (updated every step)
                self.stage_status.emit(
                    f"{label} — token {step + 1}/{total} ({pct}%)"
                )

        def _content_cb(ch_idx: int, g_chunk: int, tot_ch: int, tot_chunks: int) -> None:
            while self._paused and not self._cancelled:
                self.msleep(150)
            if self._cancelled:
                raise _Cancelled
            pct = int((g_chunk / max(tot_chunks, 1)) * 100)
            self.stage_progress.emit(2, pct, 100)
            self.chapter_running.emit(ch_idx + 1)

        def _is_cancelled() -> bool:
            return self._cancelled

        output_paths, final_path = generate_audiobook(
            book=book,
            log_cb=_tts_log,
            anchor_cb=_anchor_cb,
            content_cb=_content_cb,
            chunk_start_cb=_chunk_start_cb,
            chunk_step_cb=_chunk_step_cb,
            cancelled=_is_cancelled,
            session=session,
        )

        for ch in book.chapters:
            self.chapter_done.emit(ch.index)
        self.stage_done.emit(2)

        self.log_success.emit(
            f"Done! {len(output_paths)} chapter file(s) in {OUTPUT_DIR}"
        )
        for p in output_paths:
            self.log_info.emit(f"  Chapter → {p.name}")
        if final_path and len(output_paths) > 1:
            self.log_success.emit(f"  Complete → {final_path.name}")

        self._session_ref = session   # stash so app.py can retrieve after completion
        self.all_done.emit(output_paths, final_path)

    def get_session(self):
        """Return the BookSession after the pipeline completes."""
        return getattr(self, "_session_ref", None)


class RegenerationWorker(QThread):
    """Re-generates a single chapter using the existing voice anchor."""

    # ── Log signals ────────────────────────────────────────────────────
    log_info    = pyqtSignal(str)
    log_success = pyqtSignal(str)
    log_warn    = pyqtSignal(str)
    log_error   = pyqtSignal(str)

    # ── Chapter signals ────────────────────────────────────────────────
    chapter_running = pyqtSignal(int)
    chapter_done    = pyqtSignal(int)
    chapter_error   = pyqtSignal(int)

    # ── Completion signal ──────────────────────────────────────────────
    regen_done = pyqtSignal(int, object)   # chapter_index, final_path | None

    def __init__(self, chapter_index: int, book, session, gender: str) -> None:
        super().__init__()
        self._chapter_index = chapter_index
        self._book          = book
        self._session       = session
        self._gender        = gender
        self._cancelled     = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            self._run_regen()
        except Exception as exc:
            self.log_error.emit(str(exc))
            self.chapter_error.emit(self._chapter_index)

    def _run_regen(self) -> None:
        from pathlib import Path
        from src.pipeline.tts_engine import (
            _chapter_title_text,
            _load_base_and_prompt,
            _merge_and_save,
            _merge_chapters,
            _resolve_device,
            _safe_filename,
        )
        from src.config import OUTPUT_DIR

        chapter = next(
            (ch for ch in self._book.chapters if ch.index == self._chapter_index),
            None,
        )
        if chapter is None:
            self.log_error.emit(f"Chapter {self._chapter_index} not found.")
            self.chapter_error.emit(self._chapter_index)
            return

        if not self._session.anchor_available():
            self.log_error.emit("Voice anchor not found — cannot regenerate.")
            self.chapter_error.emit(self._chapter_index)
            return

        device = _resolve_device(self.log_info.emit)
        anchor_path = Path(self._session.anchor_path)

        self.chapter_running.emit(self._chapter_index)

        tts, voice_prompt = _load_base_and_prompt(
            anchor_path, device, self.log_info.emit, None
        )

        safe_title = _safe_filename(self._book.title)
        safe_ch    = _safe_filename(chapter.title)
        chapter_path = OUTPUT_DIR / f"{safe_title}_ch{chapter.index:02d}_{safe_ch}.wav"

        chunk_wavs: list[tuple] = []
        pauses_out: list[float] = []

        # Title announcement
        title_text = _chapter_title_text(
            chapter.index, chapter.title, self._book.subdivision_type
        )
        try:
            wavs, sr = tts.generate_voice_clone(
                text=title_text,
                voice_clone_prompt=voice_prompt,
                language=self._book.language,
            )
            chunk_wavs.append((wavs[0], sr))
            pauses_out.append(1.0)
        except Exception as exc:
            self.log_warn.emit(f"Title announcement failed ({exc}), skipping")

        # Content chunks
        for ck_idx, chunk in enumerate(chapter.chunks):
            if self._cancelled:
                break
            if not chunk.strip():
                continue
            try:
                wavs, sr = tts.generate_voice_clone(
                    text=chunk,
                    voice_clone_prompt=voice_prompt,
                    language=self._book.language,
                )
                chunk_wavs.append((wavs[0], sr))
                pause = (
                    chapter.chunk_pauses[ck_idx]
                    if ck_idx < len(chapter.chunk_pauses)
                    else 0.6
                )
                pauses_out.append(pause)
            except Exception as exc:
                self.log_warn.emit(f"Chunk {ck_idx + 1} error ({exc}), skipping")

        if not chunk_wavs:
            self.log_error.emit(f"No audio generated for chapter {self._chapter_index}")
            self.chapter_error.emit(self._chapter_index)
            return

        _merge_and_save(chunk_wavs, chapter_path, self.log_info.emit, pauses_out)
        self._session.mark_chapter_done(self._chapter_index, chapter_path)
        self._session.save()

        self.chapter_done.emit(self._chapter_index)
        self.log_success.emit(f"Regenerated: {chapter_path.name}")

        # Re-merge complete audiobook when all chapters are done
        final_path = None
        if self._session.is_complete:
            all_paths = [
                Path(ch.output)
                for ch in self._session.chapters
                if ch.output and Path(ch.output).is_file()
            ]
            if len(all_paths) > 1:
                final_path = OUTPUT_DIR / f"{safe_title}_complete.wav"
                _merge_chapters(all_paths, final_path, self.log_info.emit)
            elif all_paths:
                final_path = all_paths[0]

        self.regen_done.emit(self._chapter_index, final_path)


class MetadataReanalyzeWorker(QThread):
    """Re-runs LLM metadata detection on the stored sample from a StructuredBook."""

    log_info       = pyqtSignal(str)
    metadata_ready = pyqtSignal(dict)
    failed         = pyqtSignal(str)

    def __init__(
        self,
        sample: str,
        model: str,
        provider: str = "ollama",
        api_key: str = "",
        ollama_url: str = "http://localhost:11434",
    ) -> None:
        super().__init__()
        self._sample    = sample
        self._model     = model
        self._provider  = provider
        self._api_key   = api_key
        self._ollama_url = ollama_url

    def run(self) -> None:
        try:
            from src.pipeline.structurer import _call_llm_for_metadata
            meta = _call_llm_for_metadata(
                self._sample,
                self._model,
                log_cb=self.log_info.emit,
                provider=self._provider,
                api_key=self._api_key,
                ollama_base_url=self._ollama_url,
            )
            if meta:
                self.metadata_ready.emit(meta)
            else:
                self.failed.emit("LLM returned no metadata")
        except Exception as exc:
            self.failed.emit(str(exc))


class _Cancelled(BaseException):
    """Internal sentinel raised when the pipeline is cancelled.

    Inherits from BaseException (not Exception) so that it propagates
    through third-party ``except Exception`` handlers (e.g. inside the
    extractor / TTS engine) without being accidentally swallowed.
    """


class VoiceDesignWorker(QThread):
    """Generates a genre voice anchor WAV in a background thread."""

    log         = pyqtSignal(str)
    progress    = pyqtSignal(float)
    finished_ok = pyqtSignal(object)   # Path
    failed      = pyqtSignal(str)

    def __init__(
        self,
        genre: str,
        language: str = "en",
        voice_instruct: str = "",
    ) -> None:
        super().__init__()
        self._genre          = genre
        self._language       = language
        self._voice_instruct = voice_instruct
        self._cancelled      = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            from src.pipeline.tts_engine import generate_genre_voice_anchor
            path = generate_genre_voice_anchor(
                genre=self._genre,
                language=self._language,
                voice_instruct=self._voice_instruct,
                log_cb=self.log.emit,
                progress_cb=self.progress.emit,
                cancelled=lambda: self._cancelled,
            )
            if path is not None:
                self.finished_ok.emit(path)
        except Exception as exc:
            self.failed.emit(str(exc))


class VoiceFillWorker(QThread):
    """Calls the LLM to fill all voice spec fields from a natural-language prompt."""

    filled = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(
        self,
        prompt: str,
        provider: str,
        model: str,
        api_key: str = "",
        ollama_base_url: str = "http://localhost:11434",
    ) -> None:
        super().__init__()
        self._prompt          = prompt
        self._provider        = provider
        self._model           = model
        self._api_key         = api_key
        self._ollama_base_url = ollama_base_url

    def run(self) -> None:
        try:
            from src.pipeline.adapter import fill_voice_spec
            spec = fill_voice_spec(
                prompt=self._prompt,
                provider=self._provider,
                model=self._model,
                api_key=self._api_key,
                ollama_base_url=self._ollama_base_url,
            )
            self.filled.emit(spec)
        except Exception as exc:
            self.failed.emit(str(exc))
