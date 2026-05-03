"""pdf2voice — Pipeline section: expandable per-stage progress panel."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_STAGE_NAMES: dict[int, str] = {
    0: "Extraction",
    1: "Structuring",
    2: "Voice Design",
    3: "Generation",
}
_STAGE_DESCS: dict[int, str] = {
    0: "PDF → Markdown",
    1: "AI chapter detection",
    2: "Voice anchor synthesis",
    3: "Speech synthesis",
}


class _StageRow(QFrame):
    def __init__(self, stage_id: int, name: str, desc: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("stage-row")
        self._stage_id = stage_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(4)

        # ── Header row ────────────────────────────────────────────────
        hrow = QHBoxLayout()
        hrow.setSpacing(10)

        self._icon = QFrame()
        self._icon.setObjectName("stage-icon-pending")
        self._icon.setFixedSize(10, 10)
        hrow.addWidget(self._icon)

        name_lbl = QLabel(name)
        name_lbl.setObjectName("stage-name")
        hrow.addWidget(name_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setObjectName("stage-desc")
        hrow.addWidget(desc_lbl, stretch=1)

        self._state_lbl = QLabel("")
        self._state_lbl.setObjectName("stage-state-pending")
        self._state_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._state_lbl.setMinimumWidth(90)
        hrow.addWidget(self._state_lbl)

        layout.addLayout(hrow)

        # ── Progress bar ──────────────────────────────────────────────
        bar_row = QHBoxLayout()
        bar_row.setContentsMargins(30, 0, 0, 0)
        self._bar = QProgressBar()
        self._bar.setObjectName("pipeline-bar")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)
        self._bar.setVisible(False)
        bar_row.addWidget(self._bar)
        layout.addLayout(bar_row)

        # ── Detail text ───────────────────────────────────────────────
        detail_row = QHBoxLayout()
        detail_row.setContentsMargins(30, 0, 0, 0)
        self._detail_lbl = QLabel("")
        self._detail_lbl.setObjectName("stage-detail")
        self._detail_lbl.setVisible(False)
        detail_row.addWidget(self._detail_lbl)
        layout.addLayout(detail_row)

    # ── State setters ─────────────────────────────────────────────────

    def set_running(self) -> None:
        self._set_icon("stage-icon-running")
        self._set_state("stage-state-running", "Running …")
        self._bar.setRange(0, 0)
        self._bar.setVisible(True)
        self._detail_lbl.setVisible(False)

    def set_done(self) -> None:
        self._set_icon("stage-icon-done")
        self._set_state("stage-state-done", "Done")
        self._bar.setRange(0, 100)
        self._bar.setValue(100)
        self._bar.setVisible(False)
        self._detail_lbl.setVisible(False)

    def set_error(self) -> None:
        self._set_icon("stage-icon-error")
        self._set_state("stage-state-error", "Error")
        self._bar.setVisible(False)
        self._detail_lbl.setVisible(False)

    def set_cancelled(self) -> None:
        self._set_icon("stage-icon-error")
        self._set_state("stage-state-error", "Cancelled")
        self._bar.setVisible(False)
        self._detail_lbl.setVisible(False)

    def set_pending(self) -> None:
        self._set_icon("stage-icon-pending")
        self._set_state("stage-state-pending", "")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setVisible(False)
        self._detail_lbl.setVisible(False)

    def set_progress(self, value: int, maximum: int) -> None:
        if maximum == 0:
            self._bar.setRange(0, 0)
        else:
            self._bar.setRange(0, maximum)
            self._bar.setValue(value)
        self._bar.setVisible(True)

    def set_detail(self, text: str) -> None:
        if text:
            self._detail_lbl.setText(text)
            self._detail_lbl.setVisible(True)
        else:
            self._detail_lbl.setVisible(False)

    # ── Helpers ───────────────────────────────────────────────────────

    def _set_icon(self, obj_name: str) -> None:
        self._icon.setObjectName(obj_name)
        self._icon.style().unpolish(self._icon)
        self._icon.style().polish(self._icon)

    def _set_state(self, obj_name: str, text: str) -> None:
        self._state_lbl.setObjectName(obj_name)
        self._state_lbl.style().unpolish(self._state_lbl)
        self._state_lbl.style().polish(self._state_lbl)
        self._state_lbl.setText(text)


class PipelineSection(QFrame):
    """Expandable section showing per-stage pipeline progress."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pipeline-section")
        self._current_stage = -1
        self._expanded = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Section header ────────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("section-header")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 12, 16, 12)
        hl.setSpacing(10)

        self._toggle_btn = QPushButton("▾")
        self._toggle_btn.setObjectName("section-toggle-btn")
        self._toggle_btn.setFixedSize(22, 22)
        self._toggle_btn.clicked.connect(self._toggle_expand)
        hl.addWidget(self._toggle_btn)

        hdr_title = QLabel("PROCESSING PIPELINE")
        hdr_title.setObjectName("section-title")
        hl.addWidget(hdr_title)
        hl.addStretch()

        self._overall_lbl = QLabel("Idle")
        self._overall_lbl.setObjectName("pipeline-stage-lbl")
        hl.addWidget(self._overall_lbl)

        layout.addWidget(hdr)

        sep = QFrame()
        sep.setObjectName("panel-sep")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # ── Collapsible stage rows ────────────────────────────────────
        self._content = QWidget()
        self._content.setObjectName("section-content")
        cl = QVBoxLayout(self._content)
        cl.setContentsMargins(16, 4, 16, 8)
        cl.setSpacing(0)

        self._stages: dict[int, _StageRow] = {}
        for i in range(len(_STAGE_NAMES)):
            row = _StageRow(i, _STAGE_NAMES[i], _STAGE_DESCS[i])
            self._stages[i] = row
            cl.addWidget(row)
            if i < len(_STAGE_NAMES) - 1:
                sep2 = QFrame()
                sep2.setObjectName("stage-sep")
                sep2.setFixedHeight(1)
                cl.addWidget(sep2)

        layout.addWidget(self._content)

    # ── Toggle ────────────────────────────────────────────────────────

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._toggle_btn.setText("▾" if self._expanded else "▸")

    # ── Public API (compatible with old PipelinePanel) ────────────────

    def set_stage_progress(self, stage: int, value: int, maximum: int = 100) -> None:
        if row := self._stages.get(stage):
            row.set_progress(value, maximum)

    def mark_running(self, stage: int) -> None:
        self._current_stage = stage
        if row := self._stages.get(stage):
            row.set_running()
        self._overall_lbl.setText(_STAGE_NAMES.get(stage, f"Stage {stage}") + " …")
        if not self._expanded:
            self._toggle_expand()

    def mark_done(self, stage: int) -> None:
        if row := self._stages.get(stage):
            row.set_done()
        if stage == max(_STAGE_NAMES):
            self._overall_lbl.setText("Complete ✓")
        else:
            self._overall_lbl.setText(f"{_STAGE_NAMES.get(stage, '')} done")

    def mark_error(self, stage: int) -> None:
        if row := self._stages.get(stage):
            row.set_error()
        self._overall_lbl.setText("Error in " + _STAGE_NAMES.get(stage, f"stage {stage}"))

    def mark_cancelled(self) -> None:
        """Mark the currently-active stage as cancelled and update the overall label."""
        if row := self._stages.get(self._current_stage):
            row.set_cancelled()
        self._overall_lbl.setText("Cancelled")
        self._current_stage = -1

    def set_status(self, text: str) -> None:
        self._overall_lbl.setText(text)
        if row := self._stages.get(self._current_stage):
            row.set_detail(text)

    def reset_all(self) -> None:
        self._current_stage = -1
        for row in self._stages.values():
            row.set_pending()
        self._overall_lbl.setText("Idle")
