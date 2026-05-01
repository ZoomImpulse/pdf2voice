from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button, Footer, Header, Input, Label,
    RadioButton, RadioSet, Static,
)

from src.config import LLM_MODEL, OUTPUT_DIR, TTS_BASE_MODEL, TTS_DESIGN_MODEL, TTS_GENDER
from src.widgets.chapter_list import ChapterListPanel
from src.widgets.log_panel import LogPanel
from src.widgets.pipeline_panel import PipelinePanel


class GenderPanel(Static):
    DEFAULT_CSS = """
    GenderPanel {
        border: solid $primary;
        padding: 1;
        width: 18;
        height: auto;
    }
    GenderPanel Label { height: 1; margin-bottom: 1; }
    GenderPanel RadioSet { height: auto; background: transparent; border: none; }
    """

    def compose(self) -> ComposeResult:
        yield Label("Voice", classes="panel-title")
        with RadioSet(id="gender-select"):
            yield RadioButton("♀  Female", id="rb-female", value=TTS_GENDER == "female")
            yield RadioButton("♂  Male",   id="rb-male",   value=TTS_GENDER == "male")

    def get_gender(self) -> str:
        rs = self.query_one(RadioSet)
        return "female" if rs.pressed_button and rs.pressed_button.id == "rb-female" else "male"


class SettingsPanel(Static):
    DEFAULT_CSS = """
    SettingsPanel {
        border: solid $primary;
        padding: 1;
        width: 32;
        height: auto;
    }
    SettingsPanel Label { height: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Label("Settings", classes="panel-title")
        yield Label(f"LLM:  [accent]{LLM_MODEL}[/accent]", markup=True)
        design_short = TTS_DESIGN_MODEL.split("/")[-1].replace("Qwen3-TTS-12Hz-", "")
        base_short   = TTS_BASE_MODEL.split("/")[-1].replace("Qwen3-TTS-12Hz-", "")
        yield Label(f"Anchor: [accent]{design_short}[/accent]", markup=True)
        yield Label(f"Base:   [accent]{base_short}[/accent]", markup=True)
        yield Label(f"Out:   [accent]{OUTPUT_DIR}[/accent]", markup=True)


class InputPanel(Static):
    DEFAULT_CSS = """
    InputPanel {
        border: solid $primary;
        padding: 1;
        height: auto;
        width: 1fr;
    }
    InputPanel Horizontal { height: 3; }
    InputPanel Input { width: 1fr; }
    InputPanel Button { width: 12; margin-left: 1; }
    """

    def __init__(self, initial_path: str = "") -> None:
        super().__init__()
        self._initial = initial_path

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(
                placeholder="Path to PDF file ...",
                value=self._initial,
                id="pdf-input",
            )
            yield Button("Browse", id="btn-browse", variant="default")

    def get_path(self) -> str:
        return self.query_one("#pdf-input", Input).value.strip()


class ControlBar(Static):
    DEFAULT_CSS = """
    ControlBar {
        height: 3;
        layout: horizontal;
        padding: 0 1;
        align: left middle;
    }
    ControlBar Button { margin-right: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Button("▶ Start",         id="btn-start",       variant="success")
        yield Button("⏸ Pause",         id="btn-pause",       variant="warning", disabled=True)
        yield Button("✕ Cancel",        id="btn-cancel",      variant="error",   disabled=True)
        yield Button("📂 Open Output",  id="btn-open-output", variant="default")


class Pdf2VoiceApp(App):
    CSS = """
    Screen { layout: vertical; }
    #top-row {
        layout: horizontal;
        height: auto;
        margin: 0 0 1 0;
    }
    #pipeline-row {
        height: auto;
        margin: 0 0 1 0;
    }
    #bottom-row {
        layout: horizontal;
        height: 1fr;
        margin: 0 0 1 0;
    }
    #chapter-panel { width: 40; margin-right: 1; }
    #log-panel     { width: 1fr; }
    .panel-title   { text-style: bold; margin-bottom: 1; }
    """

    TITLE = "pdf2voice"
    SUB_TITLE = "PDF → Audiobook (self-hosted)"
    BINDINGS = [
        ("ctrl+q", "quit",        "Quit"),
        ("ctrl+o", "open_output", "Open Output"),
    ]

    def __init__(self, pdf_path: str | None = None) -> None:
        super().__init__()
        self._initial_path  = pdf_path or ""
        self._pipeline_task: asyncio.Task | None = None
        self._cancelled     = False
        self._paused        = False
        self._current_stage = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="top-row"):
            yield InputPanel(self._initial_path)
            yield GenderPanel()
            yield SettingsPanel()
        with Container(id="pipeline-row"):
            yield PipelinePanel()
        with Container(id="bottom-row"):
            yield ChapterListPanel(id="chapter-panel")
            yield LogPanel(id="log-panel")
        yield ControlBar()
        yield Footer()

    # ── Events ────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-start":       self._start_pipeline()
            case "btn-pause":       self._toggle_pause()
            case "btn-cancel":      self._cancel_pipeline()
            case "btn-open-output": self.action_open_output()
            case "btn-browse":      self._browse_pdf()

    def action_open_output(self) -> None:
        path = str(OUTPUT_DIR.resolve())
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _browse_pdf(self) -> None:
        import threading

        def _dialog() -> None:
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.wm_attributes("-topmost", True)
                path = filedialog.askopenfilename(
                    title="Select PDF",
                    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                )
                root.destroy()
                if path:
                    self.call_from_thread(self._set_pdf_path, path)
            except Exception as exc:
                self.call_from_thread(self._log().error, f"Browse error: {exc}")

        threading.Thread(target=_dialog, daemon=True).start()

    def _set_pdf_path(self, path: str) -> None:
        self.query_one("#pdf-input", Input).value = path

    # ── Pipeline control ──────────────────────────────────────────────

    def _start_pipeline(self) -> None:
        pdf_path = self.query_one(InputPanel).get_path()
        if not pdf_path:
            self._log().error("Please select a PDF file first.")
            return
        if not Path(pdf_path).is_file():
            self._log().error(f"File not found: {pdf_path}")
            return

        self._cancelled = False
        self._paused    = False
        self._set_controls(running=True)
        self._pipeline().reset_all()
        self._chapters().clear()
        self._log().clear()

        gender = self.query_one(GenderPanel).get_gender()
        self._pipeline_task = asyncio.create_task(
            self._run_pipeline(pdf_path, gender), name="pipeline"
        )

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        self.query_one("#btn-pause", Button).label = "▶ Resume" if self._paused else "⏸ Pause"

    def _cancel_pipeline(self) -> None:
        self._cancelled = True
        if self._pipeline_task:
            self._pipeline_task.cancel()
        self._set_controls(running=False)
        self._log().error("Pipeline cancelled.")

    # ── Pipeline coroutine ────────────────────────────────────────────

    async def _run_pipeline(self, pdf_path: str, gender: str) -> None:
        from src.pipeline.extractor import count_pages, extract_pdf
        from src.pipeline.structurer import structure_content
        from src.pipeline.tts_engine import generate_audiobook

        log      = self._log()
        pipeline = self._pipeline()
        chapters = self._chapters()

        try:
            # ── Stage 0: PDF Extraction ──────────────────────────────
            self._current_stage = 0
            pipeline.mark_running(0)
            log.info(f"Extracting PDF: {pdf_path}")

            total_pages = await asyncio.get_event_loop().run_in_executor(
                None, count_pages, pdf_path
            )
            log.info(f"Found: {total_pages} pages")

            def _extract_cb(cur: int, tot: int) -> None:
                self.call_from_thread(
                    pipeline.set_stage_progress, 0,
                    (cur / max(tot, 1)) * 100, f"{cur}/{tot}"
                )

            markdown = await asyncio.get_event_loop().run_in_executor(
                None, extract_pdf, pdf_path, _extract_cb
            )
            pipeline.mark_done(0)
            log.success(f"PDF extracted ({len(markdown):,} characters)")
            await self._check_cancel()

            # ── Stage 1: LLM Structuring ─────────────────────────────
            self._current_stage = 1
            pipeline.mark_running(1)
            log.info(f"AI structuring content via {LLM_MODEL} ...")

            def _llm_log(msg: str) -> None:
                self.call_from_thread(log.info, msg)

            book = await asyncio.get_event_loop().run_in_executor(
                None, structure_content, markdown, _llm_log
            )
            pipeline.mark_done(1)
            log.success(
                f"Structured: \"{book.title}\" — "
                f"{len(book.chapters)} chapters, {book.total_chunks} chunks"
            )
            if book.genre:
                log.info(f"Genre: {book.genre}")
            log.info(f"Voice: {book.voice_instruct}")

            chapters.load_chapters([(ch.index, ch.title) for ch in book.chapters])
            await self._check_cancel()

            # ── Stage 2: Voice Anker (VoiceDesign) ───────────────────
            self._current_stage = 2
            pipeline.mark_running(2)
            gender_label = "Female" if gender == "female" else "Male"
            log.info(f"Voice Anchor: Generating voice reference ({gender_label}) ...")

            def _anchor_cb(pct: float) -> None:
                self.call_from_thread(pipeline.set_stage_progress, 2, pct)

            def _tts_log(msg: str) -> None:
                self.call_from_thread(log.info, msg)

            def _content_cb(ch_idx: int, g_chunk: int, tot_ch: int, tot_chunks: int) -> None:
                pct = (g_chunk / max(tot_chunks, 1)) * 100
                self.call_from_thread(pipeline.set_stage_progress, 3, pct)
                self.call_from_thread(chapters.set_running, ch_idx + 1)

            def _is_cancelled() -> bool:
                return self._cancelled

            _anchor_done = False

            def _anchor_cb_with_switch(pct: float) -> None:
                nonlocal _anchor_done
                self.call_from_thread(pipeline.set_stage_progress, 2, pct)
                if pct >= 100.0 and not _anchor_done:
                    _anchor_done = True
                    self.call_from_thread(pipeline.mark_done, 2)
                    self.call_from_thread(pipeline.mark_running, 3)

            output_paths, final_path = await asyncio.get_event_loop().run_in_executor(
                None,
                generate_audiobook,
                book,
                gender,
                _tts_log,
                _anchor_cb_with_switch,
                _content_cb,
                _is_cancelled,
            )

            for ch in book.chapters:
                chapters.set_done(ch.index)

            pipeline.mark_done(3)
            log.success(f"Done! {len(output_paths)} chapter file(s) in {OUTPUT_DIR}")
            for p in output_paths:
                log.info(f"  Chapter → {p.name}")
            if final_path and len(output_paths) > 1:
                log.success(f"  Complete → {final_path.name}")

        except asyncio.CancelledError:
            pass
        except Exception as exc:
            log.error(f"Error: {exc}")
            pipeline.mark_error(self._current_stage)
        finally:
            self._set_controls(running=False)

    async def _check_cancel(self) -> None:
        if self._cancelled:
            raise asyncio.CancelledError
        while self._paused:
            await asyncio.sleep(0.2)

    # ── Helpers ───────────────────────────────────────────────────────

    def _set_controls(self, running: bool) -> None:
        self.query_one("#btn-start",  Button).disabled = running
        self.query_one("#btn-pause",  Button).disabled = not running
        self.query_one("#btn-cancel", Button).disabled = not running

    def _log(self)      -> LogPanel:       return self.query_one("#log-panel",     LogPanel)
    def _pipeline(self) -> PipelinePanel:  return self.query_one(PipelinePanel)
    def _chapters(self) -> ChapterListPanel: return self.query_one("#chapter-panel", ChapterListPanel)
