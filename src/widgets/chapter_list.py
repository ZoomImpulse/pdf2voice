from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, ListView, ListItem, Static


ICON_PENDING = "○"
ICON_RUNNING = "⟳"
ICON_DONE    = "✓"
ICON_ERROR   = "✗"


class ChapterItem(ListItem):
    DEFAULT_CSS = """
    ChapterItem {
        height: 1;
        padding: 0 1;
    }
    ChapterItem Label { width: 1fr; }
    ChapterItem.done    Label { color: $success; }
    ChapterItem.running Label { color: $accent; }
    ChapterItem.error   Label { color: $error; }
    """

    def __init__(self, index: int, title: str) -> None:
        super().__init__()
        self._index = index
        self._title = title
        self._icon  = ICON_PENDING

    def compose(self) -> ComposeResult:
        yield Label(self._render_text())

    def _render_text(self) -> str:
        short = self._title[:35] + "…" if len(self._title) > 36 else self._title
        return f"{self._icon} Ch. {self._index}: {short}"

    def _refresh_label(self) -> None:
        self.query_one(Label).update(self._render_text())

    def set_running(self) -> None:
        self._icon = ICON_RUNNING
        self.remove_class("done", "error")
        self.add_class("running")
        self._refresh_label()

    def set_done(self) -> None:
        self._icon = ICON_DONE
        self.remove_class("running", "error")
        self.add_class("done")
        self._refresh_label()

    def set_error(self) -> None:
        self._icon = ICON_ERROR
        self.remove_class("running", "done")
        self.add_class("error")
        self._refresh_label()


class ChapterListPanel(Static):
    DEFAULT_CSS = """
    ChapterListPanel {
        border: solid $primary;
        height: 1fr;
        padding: 0;
    }
    ChapterListPanel ListView {
        height: 1fr;
        background: transparent;
    }
    """

    def compose(self) -> ComposeResult:
        yield ListView()

    def load_chapters(self, chapters: list[tuple[int, str]]) -> None:
        lv = self.query_one(ListView)
        lv.clear()
        for idx, title in chapters:
            lv.append(ChapterItem(idx, title))

    def _item(self, chapter_idx: int) -> ChapterItem | None:
        for item in self.query(ChapterItem):
            if item._index == chapter_idx:
                return item
        return None

    def set_running(self, chapter_idx: int) -> None:
        item = self._item(chapter_idx)
        if item:
            item.set_running()
            self.query_one(ListView).scroll_to_widget(item)

    def set_done(self, chapter_idx: int) -> None:
        item = self._item(chapter_idx)
        if item:
            item.set_done()

    def set_error(self, chapter_idx: int) -> None:
        item = self._item(chapter_idx)
        if item:
            item.set_error()

    def clear(self) -> None:
        self.query_one(ListView).clear()
