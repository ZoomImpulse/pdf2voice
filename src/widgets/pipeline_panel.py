from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt


STAGE_LABELS = [
    "PDF Extraction",
    "AI Structuring",
    "Voice Anchor",
    "TTS Content",
]


class _StageRow(QWidget):
    def __init__(self, index: int, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        num = QLabel(str(index + 1))
        num.setObjectName("stage-num")
        num.setFixedWidth(18)
        layout.addWidget(num)

        name = QLabel(label)
        name.setObjectName("stage-name")
        name.setFixedWidth(130)
        layout.addWidget(name)

        self._bar = QProgressBar()
        self._bar.setObjectName("stage-bar")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        layout.addWidget(self._bar)

        self._status = QLabel("—")
        self._status.setObjectName("stage-status")
        self._status.setFixedWidth(52)
        self._status.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._status)

    def set_progress(self, value: int, maximum: int) -> None:
        self._bar.setRange(0, max(maximum, 1))
        self._bar.setValue(value)

    def set_status(self, text: str, variant: str = "") -> None:
        self._status.setText(text)
        name = f"stage-status-{variant}" if variant else "stage-status"
        self._status.setObjectName(name)
        # Force QSS re-evaluation
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def reset(self) -> None:
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self.set_status("—")


class PipelinePanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pipeline-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)

        title = QLabel("Pipeline")
        title.setObjectName("panel-title")
        layout.addWidget(title)

        self._rows: list[_StageRow] = []
        for i, label in enumerate(STAGE_LABELS):
            row = _StageRow(i, label)
            self._rows.append(row)
            layout.addWidget(row)

    def set_stage_progress(self, stage: int, value: int, maximum: int = 100) -> None:
        self._rows[stage].set_progress(value, maximum)

    def mark_running(self, stage: int) -> None:
        self._rows[stage].set_progress(0, 100)
        self._rows[stage].set_status("…", "running")

    def mark_done(self, stage: int) -> None:
        self._rows[stage].set_progress(100, 100)
        self._rows[stage].set_status("✓", "done")

    def mark_error(self, stage: int) -> None:
        self._rows[stage].set_progress(0, 100)
        self._rows[stage].set_status("✗", "error")

    def reset_all(self) -> None:
        for row in self._rows:
            row.reset()
