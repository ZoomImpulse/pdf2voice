from __future__ import annotations

from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit


class LogPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("log-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("Activity Log")
        title.setObjectName("panel-title")
        layout.addWidget(title)

        self._text = QTextEdit()
        self._text.setObjectName("log-text")
        self._text.setReadOnly(True)
        layout.addWidget(self._text)

    # ── Public API ────────────────────────────────────────────────────

    def info(self, message: str) -> None:
        self._append(f'<span style="color:#94a3b8">{self._esc(message)}</span>')

    def success(self, message: str) -> None:
        self._append(f'<span style="color:#22c55e">{self._esc(message)}</span>')

    def warn(self, message: str) -> None:
        self._append(f'<span style="color:#f59e0b">{self._esc(message)}</span>')

    def error(self, message: str) -> None:
        self._append(
            f'<span style="color:#ef4444;font-weight:600">{self._esc(message)}</span>'
        )

    def clear(self) -> None:
        self._text.clear()

    # ── Helpers ───────────────────────────────────────────────────────

    def _append(self, html: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._text.append(
            f'<span style="color:#334155">{ts}</span>&nbsp;{html}'
        )
        sb = self._text.verticalScrollBar()
        sb.setValue(sb.maximum())

    @staticmethod
    def _esc(text: str) -> str:
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
