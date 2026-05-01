"""Book generation session — persists pipeline state so a run can be resumed.

Session file location: OUTPUT_DIR/.session_<pdf_hash>.json
The pdf_hash is a 16-char SHA-256 prefix, unique enough for local use.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

SESSION_VERSION = 1


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ChapterState:
    index: int
    title: str
    chunks: list[str]
    done: bool = False
    output: str | None = None  # absolute path to the chapter .wav file


@dataclass
class BookSession:
    version: int
    pdf_hash: str
    pdf_path: str
    title: str
    gender: str
    language: str
    genre: str
    subdivision_type: str
    voice_instruct: str
    anchor_path: str | None
    chapters: list[ChapterState] = field(default_factory=list)

    # ── Queries ───────────────────────────────────────────────────────

    @property
    def completed_count(self) -> int:
        return sum(
            1 for ch in self.chapters
            if ch.done and ch.output and Path(ch.output).is_file()
        )

    @property
    def is_complete(self) -> bool:
        return bool(self.chapters) and all(
            ch.done and ch.output and Path(ch.output).is_file()
            for ch in self.chapters
        )

    def anchor_available(self) -> bool:
        return bool(self.anchor_path) and Path(self.anchor_path).is_file()

    def chapter_state(self, index: int) -> ChapterState | None:
        for ch in self.chapters:
            if ch.index == index:
                return ch
        return None

    # ── Mutations ─────────────────────────────────────────────────────

    def set_anchor(self, path: Path) -> None:
        self.anchor_path = str(path)

    def mark_chapter_done(self, index: int, output_path: Path) -> None:
        ch = self.chapter_state(index)
        if ch:
            ch.done = True
            ch.output = str(output_path)

    # ── Persistence ───────────────────────────────────────────────────

    def save(self) -> None:
        path = _session_path(self.pdf_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def delete(self) -> None:
        _session_path(self.pdf_hash).unlink(missing_ok=True)

    @staticmethod
    def load(pdf_hash_str: str) -> BookSession | None:
        path = _session_path(pdf_hash_str)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") != SESSION_VERSION:
                return None
            data["chapters"] = [ChapterState(**ch) for ch in data.pop("chapters", [])]
            return BookSession(**data)
        except Exception:
            return None


# ── Public helpers ────────────────────────────────────────────────────────────

def compute_pdf_hash(pdf_path: str | Path) -> str:
    """Return a 16-char SHA-256 hex prefix of the PDF file contents."""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()[:16]


def create_session(book, pdf_hash_str: str, pdf_path: str, gender: str) -> BookSession:
    """Build a fresh BookSession from a StructuredBook (before any TTS)."""
    from src.pipeline.structurer import StructuredBook  # avoid circular import at module level
    chapters = [
        ChapterState(index=ch.index, title=ch.title, chunks=ch.chunks)
        for ch in book.chapters
    ]
    return BookSession(
        version=SESSION_VERSION,
        pdf_hash=pdf_hash_str,
        pdf_path=pdf_path,
        title=book.title,
        gender=gender,
        language=book.language,
        genre=book.genre,
        subdivision_type=book.subdivision_type,
        voice_instruct=book.voice_instruct,
        anchor_path=None,
        chapters=chapters,
    )


def book_from_session(session: BookSession):
    """Reconstruct a StructuredBook from a saved BookSession (for resume)."""
    from src.pipeline.structurer import Chapter, StructuredBook
    chapters = [
        Chapter(index=ch.index, title=ch.title, chunks=ch.chunks)
        for ch in session.chapters
    ]
    return StructuredBook(
        title=session.title,
        language=session.language,
        genre=session.genre,
        subdivision_type=session.subdivision_type,
        voice_instruct=session.voice_instruct,
        chapters=chapters,
    )


# ── Internal ──────────────────────────────────────────────────────────────────

def _session_path(pdf_hash_str: str) -> Path:
    from src.config import OUTPUT_DIR
    return OUTPUT_DIR / f".session_{pdf_hash_str}.json"
