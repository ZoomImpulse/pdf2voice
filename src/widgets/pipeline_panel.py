from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, ProgressBar, Static
from textual.containers import Vertical


STAGE_LABELS = [
    "PDF Extraction",
    "AI Structuring",
    "Voice Anchor",
    "TTS Content",
]

STATUS_IDLE    = "idle"
STATUS_RUNNING = "..."
STATUS_DONE    = "✓"
STATUS_ERROR   = "✗"


class StageRow(Static):
    DEFAULT_CSS = """
    StageRow {
        height: 2;
        layout: horizontal;
        padding: 0 1;
    }
    StageRow Label.stage-name {
        width: 22;
        content-align: left middle;
    }
    StageRow ProgressBar {
        width: 1fr;
    }
    StageRow Label.stage-status {
        width: 10;
        content-align: right middle;
    }
    """

    def __init__(self, index: int, label: str) -> None:
        super().__init__()
        self._index = index
        self._label = label

    def compose(self) -> ComposeResult:
        yield Label(f"[{self._index + 1}] {self._label}", classes="stage-name")
        yield ProgressBar(total=100, show_eta=False, show_percentage=False)
        yield Label(STATUS_IDLE, classes="stage-status")

    def set_progress(self, value: float, status: str | None = None) -> None:
        self.query_one(ProgressBar).progress = value
        if status is not None:
            self.query_one(".stage-status", Label).update(status)

    def reset(self) -> None:
        self.set_progress(0, STATUS_IDLE)


class PipelinePanel(Static):
    DEFAULT_CSS = """
    PipelinePanel {
        border: solid $primary;
        padding: 1;
        height: auto;
    }
    PipelinePanel > Vertical {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            for i, label in enumerate(STAGE_LABELS):
                yield StageRow(i, label)

    def _row(self, stage: int) -> StageRow:
        return self.query(StageRow)[stage]

    def set_stage_progress(self, stage: int, percent: float, status: str | None = None) -> None:
        self._row(stage).set_progress(percent, status)

    def mark_running(self, stage: int) -> None:
        self.set_stage_progress(stage, 0, STATUS_RUNNING)

    def mark_done(self, stage: int) -> None:
        self.set_stage_progress(stage, 100, STATUS_DONE)

    def mark_error(self, stage: int) -> None:
        self.set_stage_progress(stage, 0, STATUS_ERROR)

    def reset_all(self) -> None:
        for row in self.query(StageRow):
            row.reset()
