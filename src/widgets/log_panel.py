from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import RichLog, Static


class LogPanel(Static):
    DEFAULT_CSS = """
    LogPanel {
        border: solid $primary;
        height: 1fr;
        padding: 0;
    }
    LogPanel RichLog {
        height: 1fr;
        background: transparent;
    }
    """

    def compose(self) -> ComposeResult:
        yield RichLog(wrap=True, highlight=False, markup=True, auto_scroll=True)

    def _log(self) -> RichLog:
        return self.query_one(RichLog)

    def info(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log().write(f"[dim]{ts}[/dim] {message}")

    def success(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log().write(f"[dim]{ts}[/dim] [green]{message}[/green]")

    def error(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log().write(f"[dim]{ts}[/dim] [red bold]{message}[/red bold]")

    def clear(self) -> None:
        self._log().clear()
