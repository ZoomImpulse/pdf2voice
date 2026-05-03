from __future__ import annotations

import gc
import re
from pathlib import Path
from typing import Callable

import soundfile as sf
import torch

from src.config import (
    OUTPUT_DIR,
    TTS_BASE_MODEL,
    TTS_DESIGN_MODEL,
    TTS_DEVICE,
    TTS_VOICE_INSTRUCT,
)
from src.pipeline.structurer import StructuredBook
from src.pipeline.session import BookSession, chunk_temp_path

ChunkCallback = Callable[[int, int, int, int], None]

_SILENCE_TITLE_S: float = 1.0  # pause after chapter title announcement
_SILENCE_CHUNK_S: float = 0.6  # fallback when chunk_pauses is missing

_ANCHOR_TEXTS: dict[str, str] = {
    "de": (
        "Willkommen zu diesem Hörbuch. Ich werde Ihr Vorleser auf dieser Reise sein. "
        "Diese Geschichte nimmt Sie mit auf eine unvergessliche Reise durch Worte und Gedanken."
    ),
    "en": (
        "Welcome to this audiobook. I will be your narrator throughout this journey. "
        "This story will take you on an unforgettable adventure through words and ideas."
    ),
}
_ANCHOR_TEXT_DEFAULT = (
    "Willkommen zu diesem Hörbuch. Ich werde Ihr Vorleser auf dieser Reise sein. "
    "Welcome to this audiobook. I will be your narrator throughout this journey."
)


def generate_audiobook(
    book: StructuredBook,
    gender: str = "female",
    log_cb: Callable[[str], None] | None = None,
    anchor_cb: Callable[[float], None] | None = None,
    content_cb: ChunkCallback | None = None,
    cancelled: Callable[[], bool] | None = None,
    session: BookSession | None = None,
) -> tuple[list[Path], Path | None]:
    """Two-phase audiobook generation for consistent voice throughout.

    Phase 1 — VoiceDesign: generates a short voice anchor clip.
    Phase 2 — Base:        clones the anchor voice for all content chunks.

    Pass a BookSession to enable resume: completed chapters are skipped and
    progress is persisted after every chapter so the run can be interrupted
    and continued later.

    Returns (chapter_paths, final_merged_path).
    """
    device         = _resolve_device(log_cb)
    voice_instruct = _gender_instruction(book.voice_instruct or TTS_VOICE_INSTRUCT, gender)
    safe_title     = _safe_filename(book.title)

    # ── Persistent anchor path (reused across sessions) ───────────────
    persist_anchor = (
        OUTPUT_DIR / f".voice_anchor_{session.pdf_hash}.wav"
        if session else OUTPUT_DIR / ".voice_anchor.wav"
    )

    # ── Phase 1: Voice anchor ─────────────────────────────────────────
    if session and session.anchor_available():
        anchor_path: Path | None = Path(session.anchor_path)  # type: ignore[arg-type]
        if log_cb:
            log_cb(f"Voice Anchor: Reusing saved anchor ({anchor_path.name})")
        if anchor_cb:
            anchor_cb(100.0)
    else:
        anchor_path = _generate_anchor(
            voice_instruct, book.language, device, log_cb, anchor_cb, cancelled,
            output_path=persist_anchor,
        )
        if anchor_path is None:
            return [], None
        if session:
            session.set_anchor(anchor_path)
            session.save()

    # ── Phase 2: Base model + voice clone prompt ──────────────────────
    tts, voice_prompt = _load_base_and_prompt(anchor_path, device, log_cb, anchor_cb)

    # ── Phase 3: Generate content chunks ─────────────────────────────
    output_paths: list[Path] = []
    total_chapters = len(book.chapters)
    total_chunks   = book.total_chunks
    global_chunk   = 0

    for ch_idx, chapter in enumerate(book.chapters):
        if cancelled and cancelled():
            if log_cb:
                log_cb("TTS: Cancelled")
            break

        safe_ch      = _safe_filename(chapter.title)
        chapter_path = OUTPUT_DIR / f"{safe_title}_ch{chapter.index:02d}_{safe_ch}.wav"

        # ── Skip already-completed chapters (resume mode) ─────────────
        if session is not None:
            ch_state = session.chapter_state(chapter.index)
            if ch_state and ch_state.done and chapter_path.is_file():
                if log_cb:
                    log_cb(
                        f"TTS: Chapter {chapter.index}/{total_chapters} — "
                        f"{chapter.title} (skipped, already done)"
                    )
                output_paths.append(chapter_path)
                global_chunk += len(chapter.chunks)
                if content_cb:
                    content_cb(ch_idx, global_chunk, total_chapters, total_chunks)
                continue

        if log_cb:
            log_cb(f"TTS: Chapter {chapter.index}/{total_chapters} — {chapter.title}")

        chunk_wavs: list[tuple[object, int]] = []
        chunk_pauses_out: list[float] = []

        # ── Chapter title announcement ────────────────────────────────
        title_text = _chapter_title_text(chapter.index, chapter.title, book.subdivision_type)
        try:
            wavs, sr = tts.generate_voice_clone(
                text=title_text,
                voice_clone_prompt=voice_prompt,
                language=_resolve_language(book.language),
            )
            chunk_wavs.append((wavs[0], sr))
            chunk_pauses_out.append(_SILENCE_TITLE_S)
        except Exception as exc:
            if log_cb:
                log_cb(f"TTS: Chapter title error ({exc}), skipping title")

        for ck_idx, chunk_text in enumerate(chapter.chunks):
            if cancelled and cancelled():
                break
            if not chunk_text.strip():
                global_chunk += 1
                continue

            try:
                wavs, sr = tts.generate_voice_clone(
                    text=chunk_text,
                    voice_clone_prompt=voice_prompt,
                    language=_resolve_language(book.language),
                )
                chunk_wavs.append((wavs[0], sr))
                pause = (
                    chapter.chunk_pauses[ck_idx]
                    if ck_idx < len(chapter.chunk_pauses)
                    else _SILENCE_CHUNK_S
                )
                chunk_pauses_out.append(pause)
            except Exception as exc:
                if log_cb:
                    log_cb(f"TTS: Chunk error ({exc}), skipping")
                global_chunk += 1
                continue

            global_chunk += 1
            if content_cb:
                content_cb(ch_idx, global_chunk, total_chapters, total_chunks)
            if log_cb:
                log_cb(
                    f"TTS: Chunk {ck_idx + 1}/{len(chapter.chunks)} "
                    f"({len(chunk_text)} chars) done"
                )

        if chunk_wavs:
            _merge_and_save(chunk_wavs, chapter_path, log_cb, chunk_pauses_out)
            output_paths.append(chapter_path)
            if session is not None:
                session.mark_chapter_done(chapter.index, chapter_path)
                session.save()

    # ── Phase 4: Merge chapters ───────────────────────────────────────
    final_path: Path | None = None
    if len(output_paths) > 1:
        final_path = OUTPUT_DIR / f"{safe_title}_complete.wav"
        _merge_chapters(output_paths, final_path, log_cb)
    elif output_paths:
        final_path = output_paths[0]

    # Delete transient anchor only (no session); persistent sessions are
    # managed by the caller (app.py) so regeneration remains possible.
    if session is None and anchor_path:
        anchor_path.unlink(missing_ok=True)

    return output_paths, final_path


# ── Phase 1 helpers ───────────────────────────────────────────────────────────

_LANG_CODE_TO_NAME: dict[str, str] = {
    "zh": "chinese",
    "en": "english",
    "fr": "french",
    "de": "german",
    "it": "italian",
    "ja": "japanese",
    "ko": "korean",
    "pt": "portuguese",
    "ru": "russian",
    "es": "spanish",
}


def _resolve_language(lang: str) -> str:
    """Normalise an ISO code or full name to the form the TTS model expects."""
    lower = lang.lower().strip()
    # Already a full name recognised by the model
    if lower in _LANG_CODE_TO_NAME.values() or lower == "auto":
        return lower
    # ISO-639-1 code (possibly with region tag like "en-US")
    code = lower.split("-")[0].split("_")[0]
    return _LANG_CODE_TO_NAME.get(code, "auto")


def _generate_anchor(
    voice_instruct: str,
    language: str,
    device: str,
    log_cb: Callable[[str], None] | None,
    anchor_cb: Callable[[float], None] | None,
    cancelled: Callable[[], bool] | None,
    output_path: Path | None = None,
) -> Path | None:
    from qwen_tts import Qwen3TTSModel

    anchor_text = _ANCHOR_TEXTS.get(language.lower(), _ANCHOR_TEXT_DEFAULT)
    language = _resolve_language(language)

    if log_cb:
        log_cb(f"Voice Anchor: Loading model {TTS_DESIGN_MODEL} …")
    if anchor_cb:
        anchor_cb(5.0)

    tts = Qwen3TTSModel.from_pretrained(
        TTS_DESIGN_MODEL,
        device_map=device,
        dtype=torch.bfloat16 if device != "cpu" else torch.float32,
    )

    if cancelled and cancelled():
        return None

    if log_cb:
        log_cb("Voice Anchor: Model loaded — generating voice reference …")
    if anchor_cb:
        anchor_cb(35.0)

    wavs, sr = tts.generate_voice_design(
        text=anchor_text,
        instruct=voice_instruct,
        language=language,
    )

    anchor_path = output_path or (OUTPUT_DIR / ".voice_anchor.wav")
    sf.write(str(anchor_path), wavs[0], sr)

    if log_cb:
        log_cb(f"Voice Anchor: Reference saved ({len(wavs[0]) / sr:.1f}s)")
    if anchor_cb:
        anchor_cb(60.0)

    if log_cb:
        log_cb("Voice Anchor: Unloading VoiceDesign model …")
    del tts
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if anchor_cb:
        anchor_cb(70.0)

    return anchor_path


def _load_base_and_prompt(
    anchor_path: Path,
    device: str,
    log_cb: Callable[[str], None] | None,
    anchor_cb: Callable[[float], None] | None,
) -> tuple[object, list]:
    from qwen_tts import Qwen3TTSModel

    if log_cb:
        log_cb(f"Voice Anchor: Loading TTS base model {TTS_BASE_MODEL} …")
    if anchor_cb:
        anchor_cb(75.0)

    tts = Qwen3TTSModel.from_pretrained(
        TTS_BASE_MODEL,
        device_map=device,
        dtype=torch.bfloat16 if device != "cpu" else torch.float32,
    )

    if log_cb:
        log_cb("Voice Anchor: Extracting voice profile from reference audio …")
    if anchor_cb:
        anchor_cb(90.0)

    voice_prompt = tts.create_voice_clone_prompt(
        ref_audio=str(anchor_path),
        x_vector_only_mode=True,
    )

    if log_cb:
        log_cb("Voice Anchor: Voice profile saved — voice is ready.")
    if anchor_cb:
        anchor_cb(100.0)

    return tts, voice_prompt


# ── Shared helpers ────────────────────────────────────────────────────────────

def _chapter_title_text(index: int, title: str, subdivision_type: str) -> str:
    label = f"{subdivision_type} {index}"
    return f"{label} – {title}" if title.strip() else label


def _gender_instruction(instruct: str, gender: str) -> str:
    label = "female" if gender.lower().startswith("f") else "male"
    return f"Speak as a {label} narrator. {instruct}"


def _resolve_device(log_cb: Callable[[str], None] | None = None) -> str:
    wanted = TTS_DEVICE.lower()
    if wanted.startswith("cuda"):
        if not torch.cuda.is_available():
            if log_cb:
                log_cb("TTS: CUDA not available — falling back to CPU.")
            return "cpu"
        if log_cb:
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory // (1024 ** 3)
            log_cb(f"TTS: GPU — {name} ({vram} GB VRAM)")
    return wanted


def _normalize_rms(wav: "np.ndarray", target_rms: float = 0.08) -> "np.ndarray":
    import numpy as np
    rms = float(np.sqrt(np.mean(wav ** 2)))
    if rms < 1e-6:
        return wav
    return np.clip(wav * (target_rms / rms), -1.0, 1.0)


def _merge_and_save(
    chunk_wavs: list[tuple[object, int]],
    output: Path,
    log_cb: Callable[[str], None] | None = None,
    pauses: list[float] | None = None,
) -> None:
    import numpy as np

    sr = chunk_wavs[0][1]
    parts: list[np.ndarray] = []
    for i, (wav, _) in enumerate(chunk_wavs):
        parts.append(_normalize_rms(np.asarray(wav, dtype=np.float32)))
        if i < len(chunk_wavs) - 1:
            pause_s = pauses[i] if pauses and i < len(pauses) else _SILENCE_CHUNK_S
            parts.append(np.zeros(int(pause_s * sr), dtype=np.float32))

    combined = np.concatenate(parts)
    sf.write(str(output), combined, sr)
    if log_cb:
        log_cb(f"TTS: Saved → {output.name} ({len(combined) / sr:.1f}s)")


def _merge_chapters(
    chapter_paths: list[Path],
    output: Path,
    log_cb: Callable[[str], None] | None = None,
) -> None:
    import numpy as np

    if log_cb:
        log_cb(f"TTS: Merging {len(chapter_paths)} chapters ...")

    parts: list[np.ndarray] = []
    sr: int | None = None
    for i, path in enumerate(chapter_paths):
        data, file_sr = sf.read(str(path), dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
        if sr is None:
            sr = file_sr
        parts.append(data)
        if i < len(chapter_paths) - 1:
            parts.append(np.zeros(int(3.0 * sr), dtype=np.float32))

    combined = np.concatenate(parts)
    sf.write(str(output), combined, sr)
    if log_cb:
        m, s = divmod(int(len(combined) / sr), 60)
        log_cb(f"TTS: Full audiobook saved → {output.name} ({m}m {s}s)")


def _safe_filename(name: str, max_len: int = 60) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:max_len]
