from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit


class PreviewPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("preview-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("Chapter Preview")
        title.setObjectName("panel-title")
        layout.addWidget(title)

        self._text = QTextEdit()
        self._text.setObjectName("preview-text")
        self._text.setReadOnly(True)
        layout.addWidget(self._text)

    # ── Public API ────────────────────────────────────────────────────

    def clear(self) -> None:
        self._text.clear()

    def show_placeholder(
        self, message: str = "Select a chapter to preview its TTS content."
    ) -> None:
        self._text.setHtml(
            f'<span style="color:#475569">{self._esc(message)}</span>'
        )

    def show_chapter(
        self,
        index: int,
        title: str,
        chunks: list[str],
        subdivision_type: str,
        title_announcement: str,
    ) -> None:
        label = f"{subdivision_type} {index}"
        full  = f"{label} \u2013 {title}" if title.strip() else label
        total_chars = sum(len(c) for c in chunks)
        chunk_word  = "chunk" if len(chunks) == 1 else "chunks"

        parts: list[str] = []
        parts.append(
            f'<h3 style="color:#a78bfa;margin:0 0 4px 0">{self._esc(full)}</h3>'
        )
        parts.append(
            f'<p style="color:#475569;margin:0 0 12px 0">'
            f'{len(chunks)} {chunk_word} &middot; {total_chars:,} chars</p>'
        )
        parts.append(
            '<p style="color:#64748b;font-weight:600;margin:0 0 4px 0">'
            '\u2500\u2500 Title announcement \u2500\u2500</p>'
        )
        parts.append(
            f'<p style="color:#fbbf24;font-style:italic;margin:0 0 14px 0">'
            f'{self._esc(title_announcement)}</p>'
        )
        for i, chunk in enumerate(chunks, start=1):
            parts.append(
                f'<p style="color:#475569;font-weight:600;margin:0 0 4px 0">'
                f'\u2500\u2500 Chunk {i}/{len(chunks)} ({len(chunk):,} chars) \u2500\u2500</p>'
            )
            parts.append(
                f'<p style="color:#cbd5e1;margin:0 0 14px 0">'
                f'{self._esc(chunk)}</p>'
            )

        self._text.setHtml("".join(parts))
        self._text.verticalScrollBar().setValue(0)

    # ── Helper ────────────────────────────────────────────────────────

    @staticmethod
    def _esc(text: str) -> str:
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
