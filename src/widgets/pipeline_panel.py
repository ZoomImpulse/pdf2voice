from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer


# Human-readable descriptions shown while each stage is active.
_STAGE_RUNNING: dict[int, str] = {
    0: "Extracting PDF …",
    1: "Structuring with AI …",
    2: "Preparing voice …",
    3: "Generating speech …",
}
_STAGE_DONE: dict[int, str] = {
    0: "PDF extracted",
    1: "Structuring done",
    2: "Voice ready",
    3: "All done",
}
_SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


class PipelinePanel(QWidget):
    """Compact loading indicator: animated spinner + current-state label."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pipeline-panel")

        self._frame_idx = 0
        self._spinning = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # ── Spinner + text row ────────────────────────────────────────
        row = QHBoxLayout()
        row.setSpacing(8)

        self._spinner_lbl = QLabel(_SPINNER_FRAMES[0])
        self._spinner_lbl.setObjectName("pipeline-spinner")
        self._spinner_lbl.setFixedWidth(20)
        self._spinner_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner_lbl.setVisible(False)
        row.addWidget(self._spinner_lbl)

        self._status_lbl = QLabel("Idle")
        self._status_lbl.setObjectName("pipeline-stage-lbl")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        row.addWidget(self._status_lbl, stretch=1)

        layout.addLayout(row)

        # ── Thin progress bar ─────────────────────────────────────────
        self._bar = QProgressBar()
        self._bar.setObjectName("pipeline-bar")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)
        self._bar.setVisible(False)
        layout.addWidget(self._bar)

        # ── Timer for spinner animation ───────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)

    # ── Public API (same as old PipelinePanel) ────────────────────────

    def set_stage_progress(self, stage: int, value: int, maximum: int = 100) -> None:
        if maximum == 0:
            self._bar.setRange(0, 0)
        else:
            self._bar.setRange(0, maximum)
            self._bar.setValue(value)
        self._bar.setVisible(True)

    def mark_running(self, stage: int) -> None:
        self._status_lbl.setText(_STAGE_RUNNING.get(stage, "Running …"))
        self._bar.setRange(0, 0)   # indeterminate until real progress arrives
        self._bar.setVisible(True)
        self._start_spinner()

    def mark_done(self, stage: int) -> None:
        self._status_lbl.setText(_STAGE_DONE.get(stage, "Done"))
        self._bar.setRange(0, 100)
        self._bar.setValue(100)
        # Keep spinner running until the next mark_running or reset_all
        if stage == max(_STAGE_DONE):
            self._stop_spinner()
            self._bar.setVisible(False)

    def mark_error(self, stage: int) -> None:
        stage_name = _STAGE_RUNNING.get(stage, f"Stage {stage}").rstrip(" …")
        self._status_lbl.setText(f"Error in {stage_name}")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setVisible(False)
        self._stop_spinner()

    def reset_all(self) -> None:
        self._stop_spinner()
        self._status_lbl.setText("Idle")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setVisible(False)

    # ── Internal ──────────────────────────────────────────────────────

    def _start_spinner(self) -> None:
        self._spinning = True
        self._spinner_lbl.setVisible(True)
        if not self._timer.isActive():
            self._timer.start()

    def _stop_spinner(self) -> None:
        self._spinning = False
        self._timer.stop()
        self._spinner_lbl.setVisible(False)

    def _tick(self) -> None:
        self._frame_idx = (self._frame_idx + 1) % len(_SPINNER_FRAMES)
        self._spinner_lbl.setText(_SPINNER_FRAMES[self._frame_idx])
