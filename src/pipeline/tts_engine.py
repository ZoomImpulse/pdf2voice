from __future__ import annotations

import gc
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable

import numpy as np
import soundfile as sf

from src.config import (
    FISH_SPEECH_CPP_EXE,
    FISH_SPEECH_CPP_MODEL,
    FISH_SPEECH_CPP_TOKENIZER,
    FISH_SPEECH_CPP_VULKAN,
    FISH_SPEECH_CPP_PORT,
    GENRE_PROMPTS,
    GENRE_SAMPLE_TEXTS,
    OUTPUT_DIR,
    SESSIONS_DIR,
    TTS_BACKEND,
    TTS_CLONE_MODEL,
    TTS_DESIGN_MODEL,
    TTS_DEVICE,
    VOICE_ANCHORS_DIR,
)
from src.pipeline.structurer import StructuredBook
from src.pipeline.session import (
    BookSession,
    chunk_temp_path,
    cleanup_chapter_temps,
    cleanup_session_temps,
)

ChunkCallback      = Callable[[int, int, int, int], None]
StepCallback       = Callable[[int, int], None]
ChunkStartCallback = Callable[[int, int, int, int], None]

_SILENCE_TITLE_S: float = 1.0
_SILENCE_CHUNK_S: float = 0.6

# ── Qwen3-TTS model singleton cache ──────────────────────────────────────────
# The VoiceDesign model is kept alive between Voice Designer calls so it only
# loads from disk once per session instead of on every "Generate" click.
_design_model_cache: object | None = None  # Qwen3TTSModel | None
_design_model_device: str = ""


def _get_design_model(device: str, log_cb: Callable[[str], None] | None = None):
    """Return the VoiceDesign model, loading it only when the device changes or
    the first time it is requested."""
    global _design_model_cache, _design_model_device
    if _design_model_cache is not None and _design_model_device == device:
        if log_cb:
            log_cb(f"Voice Anchor: Reusing cached VoiceDesign model ({TTS_DESIGN_MODEL})")
        return _design_model_cache

    import torch
    from qwen_tts import Qwen3TTSModel

    # Evict the old model if the device changed.
    if _design_model_cache is not None:
        del _design_model_cache
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if log_cb:
        log_cb(f"Voice Anchor: Loading VoiceDesign model {TTS_DESIGN_MODEL} ...")

    kwargs: dict = {
        "device_map": device,
        "dtype": torch.bfloat16 if device != "cpu" else torch.float32,
    }
    attn = _best_attn_impl(device)
    if attn:
        kwargs["attn_implementation"] = attn

    _design_model_cache  = Qwen3TTSModel.from_pretrained(TTS_DESIGN_MODEL, **kwargs)
    _design_model_device = device
    return _design_model_cache


def unload_design_model() -> None:
    """Release the cached VoiceDesign model (call on application quit if desired)."""
    global _design_model_cache, _design_model_device
    if _design_model_cache is not None:
        import torch
        del _design_model_cache
        _design_model_cache  = None
        _design_model_device = ""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def _best_attn_impl(device: str) -> str:
    """Return the best available attention implementation for the given device.

    Prefers 'sdpa' (PyTorch 2.0+ built-in scaled_dot_product_attention — no
    extra packages needed, works on Windows) over the default eager kernel.
    Falls back to empty string (let transformers decide) on CPU or if SDPA
    is unavailable.
    """
    if not device.startswith("cuda"):
        return ""
    try:
        import torch
        # SDPA is available in all PyTorch 2.0+ builds — no C extension needed.
        if hasattr(torch.nn.functional, "scaled_dot_product_attention"):
            return "sdpa"
    except Exception:
        pass
    return ""
class _TokenCountStreamer:
    """HuggingFace-compatible streamer that counts generated codec tokens.

    Implements the ``put`` / ``end`` protocol of ``transformers.BaseStreamer``
    so it can be passed as ``streamer=...`` to any HuggingFace ``generate()``
    call, including the ones inside Qwen3TTSModel.

    At 12 Hz (Qwen3-TTS-Tokenizer-12Hz) each codec token ≈ 1/12 s of audio.
    """

    _TOKEN_RATE: int = 12  # codec tokens per second of audio

    def __init__(
        self,
        log_cb: Callable[[str], None] | None = None,
        progress_cb: Callable[[float], None] | None = None,
        estimated_tokens: int = 480,
        start_pct: float = 0.0,
        end_pct: float = 100.0,
        report_every: int = 24,  # ≈ 2 s of audio between log updates
    ) -> None:
        self._log          = log_cb
        self._progress_cb  = progress_cb
        self._est_tokens   = max(estimated_tokens, 24)
        self._start_pct    = start_pct
        self._end_pct      = end_pct
        self._report_every = report_every
        self._count        = 0
        self._last_report  = -report_every  # trigger on very first update

    def put(self, value) -> None:
        """Called by HuggingFace generate() with each new token batch."""
        try:
            import torch
            n = int(value.shape[-1]) if isinstance(value, torch.Tensor) and value.dim() >= 1 else 1
        except Exception:
            n = 1
        self._count += n

        if self._count - self._last_report >= self._report_every:
            self._last_report = self._count
            est_secs = self._count / self._TOKEN_RATE
            pct = self._start_pct + min(self._count / self._est_tokens, 1.0) * (
                self._end_pct - self._start_pct
            )
            if self._log:
                self._log(
                    f"TTS: Generating … {est_secs:.0f}s audio "
                    f"({self._count} tokens)"
                )
            if self._progress_cb:
                self._progress_cb(pct)

    def end(self) -> None:
        """Called by HuggingFace generate() when generation is complete."""
        est_secs = self._count / self._TOKEN_RATE
        if self._log:
            self._log(
                f"TTS: Audio generation done — {est_secs:.0f}s audio "
                f"({self._count} tokens)"
            )
        if self._progress_cb:
            self._progress_cb(self._end_pct)


def _estimate_tokens(text: str) -> int:
    """Rough token-count estimate for *text* at 12 Hz / 150 wpm.

    Rule: ~5.5 chars/word, 150 wpm = 2.5 words/s, 12 tokens/s → 4.8 tokens/word.
    """
    return max(48, int(len(text) / 5.5 * 4.8))


_ANCHOR_SAMPLE_TEXT = (
    "Welcome to this audiobook. I will be your narrator throughout this journey. "
    "Together we will travel through pages filled with ideas, images, and voices "
    "that I hope will stay with you long after the final chapter. "
    "Settle in, find a comfortable place, "
    "and let the story begin."
)


def generate_audiobook(
    book: StructuredBook,
    log_cb: Callable[[str], None] | None = None,
    anchor_cb: Callable[[float], None] | None = None,
    content_cb: ChunkCallback | None = None,
    chunk_start_cb: ChunkStartCallback | None = None,
    chunk_step_cb: StepCallback | None = None,
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
    safe_title = _safe_filename(book.title)

    # ── Phase 1: Voice anchor ─────────────────────────────────────────
    # Priority: 1) session anchor (resume), 2) saved genre anchor.
    # Anchors are created exclusively via the Voice Designer — this phase
    # never generates one inline.
    genre_anchor: Path | None = None
    if book.genre and book.genre in GENRE_PROMPTS:
        candidate = VOICE_ANCHORS_DIR / f"anchor_{book.genre}.wav"
        if candidate.is_file():
            genre_anchor = candidate

    if session and session.anchor_available():
        anchor_path: Path | None = Path(session.anchor_path)  # type: ignore[arg-type]
        if log_cb:
            log_cb(f"Voice Anchor: Reusing saved anchor ({anchor_path.name})")
        if anchor_cb:
            anchor_cb(100.0)
    elif genre_anchor is not None:
        anchor_path = genre_anchor
        if log_cb:
            log_cb(f"Voice Anchor: Using genre anchor for '{book.genre}'")
        if anchor_cb:
            anchor_cb(100.0)
        if session:
            session.set_anchor(anchor_path)
            session.save()
    else:
        if log_cb:
            log_cb(
                "Voice Anchor: No anchor found — use the Voice Designer to create one."
            )
        return [], None

    # Load the transcript that was saved alongside the anchor (for voice cloning).
    anchor_text = _load_anchor_text(anchor_path)

    # ── Phase 2: Initialise TTS backend ──────────────────────────────
    if TTS_BACKEND == "qwen_tts_clone":
        tts = _QwenTTSCloneWrapper(
            anchor_path=anchor_path,
            anchor_text=anchor_text,
            log_cb=log_cb,
        )
        if log_cb:
            log_cb("TTS: Qwen3-TTS-Base clone wrapper ready.")
    else:
        tts = _FishSpeechCppWrapper(
            anchor_path=anchor_path,
            anchor_text=anchor_text,
            log_cb=log_cb,
        )
        if log_cb:
            log_cb("TTS: Fish Speech s2.cpp ready.")
    if anchor_cb:
        anchor_cb(100.0)

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
        cancelled_mid_chapter = False

        # ── Chapter title announcement ────────────────────────────────
        title_text = _chapter_title_text(chapter.index, chapter.title, book.subdivision_type)
        title_temp = chunk_temp_path(session.pdf_hash, chapter.index, -1) if session else None
        if title_temp and title_temp.is_file():
            try:
                wav_data, title_sr = sf.read(str(title_temp), dtype="float32")
                chunk_wavs.append((wav_data, title_sr))
                chunk_pauses_out.append(_SILENCE_TITLE_S)
                if log_cb:
                    log_cb(f"TTS: Chapter {chapter.index} — title loaded from cache")
            except Exception:
                title_temp.unlink(missing_ok=True)
                title_temp = None
        if not (title_temp and title_temp.is_file()):
            try:
                wav_data, sr = tts.synthesise(title_text, cancelled=cancelled)
                chunk_wavs.append((wav_data, sr))
                chunk_pauses_out.append(_SILENCE_TITLE_S)
                if title_temp:
                    sf.write(str(title_temp), wav_data, sr)
            except Exception as exc:
                if log_cb:
                    log_cb(f"TTS: Chapter title error ({exc}), skipping title")

        eff_chunks = chapter.chunks
        eff_pauses = chapter.chunk_pauses
        eff_spans  = [1] * len(chapter.chunks)

        for ck_idx, (chunk_text, chunk_pause, span) in enumerate(
            zip(eff_chunks, eff_pauses, eff_spans)
        ):
            if cancelled and cancelled():
                cancelled_mid_chapter = True
                break
            if not chunk_text.strip():
                global_chunk += span
                continue

            temp_path = (
                chunk_temp_path(session.pdf_hash, chapter.index, ck_idx) if session
                else None
            )

            # ── Load from chunk cache ───────────────────────────────────
            if temp_path and temp_path.is_file():
                try:
                    wav_data, cached_sr = sf.read(str(temp_path), dtype="float32")
                    chunk_wavs.append((wav_data, cached_sr))
                    chunk_pauses_out.append(chunk_pause)
                    global_chunk += span
                    if content_cb:
                        content_cb(ch_idx, global_chunk, total_chapters, total_chunks)
                    if log_cb:
                        log_cb(
                            f"TTS: Chunk {ck_idx + 1}/{len(eff_chunks)} "
                            f"({len(chunk_text)} chars) loaded from cache"
                        )
                    continue
                except Exception:
                    temp_path.unlink(missing_ok=True)

            if chunk_start_cb:
                chunk_start_cb(ch_idx, ck_idx, len(eff_chunks), total_chapters)

            try:
                wav_data, sr = tts.synthesise(chunk_text, cancelled=cancelled)
                chunk_wavs.append((wav_data, sr))
                chunk_pauses_out.append(chunk_pause)
                if temp_path:
                    sf.write(str(temp_path), wav_data, sr)
                    session.mark_chunk_done(chapter.index, ck_idx + 1)
                    session.save()
            except Exception as exc:
                if log_cb:
                    log_cb(f"TTS: Chunk error ({exc}), skipping")
                global_chunk += span
                continue

            global_chunk += span
            if content_cb:
                content_cb(ch_idx, global_chunk, total_chapters, total_chunks)
            if log_cb:
                log_cb(
                    f"TTS: Chunk {ck_idx + 1}/{len(eff_chunks)} "
                    f"({len(chunk_text)} chars) done"
                )

        if chunk_wavs and not cancelled_mid_chapter:
            _merge_and_save(chunk_wavs, chapter_path, log_cb, chunk_pauses_out)
            output_paths.append(chapter_path)
            if session is not None:
                session.mark_chapter_done(chapter.index, chapter_path)
                cleanup_chapter_temps(session.pdf_hash, chapter.index, len(eff_chunks))
                session.save()

    # ── Phase 4: Merge chapters ───────────────────────────────────────
    final_path: Path | None = None
    if len(output_paths) > 1:
        final_path = OUTPUT_DIR / f"{safe_title}_complete.wav"
        _merge_chapters(output_paths, final_path, log_cb)  # MP3 encoded inside
    elif output_paths:
        final_path = output_paths[0]
        audio, sr = sf.read(str(final_path), dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        _to_mp3(audio, sr, final_path, log_cb)

    # Delete transient anchor only (no session); persistent sessions are
    # managed by the caller (app.py) so regeneration remains possible.
    if session is None and anchor_path:
        anchor_path.unlink(missing_ok=True)
    elif session is not None and session.is_complete:
        # All chapters done — purge any leftover temp subfolder
        cleanup_session_temps(session.pdf_hash)

    return output_paths, final_path


def generate_genre_voice_anchor(
    genre: str,
    language: str = "en",
    voice_instruct: str = "",
    log_cb: Callable[[str], None] | None = None,
    progress_cb: Callable[[float], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> Path | None:
    """Generate and persist a voice anchor WAV for a specific genre using Qwen3 VoiceDesign.

    The VoiceDesign model is cached across calls so subsequent Generate clicks in
    the Voice Designer are fast (model stays in GPU/CPU memory after first load).

    Writes VOICE_ANCHORS_DIR/anchor_{genre}.wav  (+ .txt sidecar).
    Returns the WAV path, or None on failure/cancellation.
    """
    sample   = GENRE_SAMPLE_TEXTS.get(genre, _ANCHOR_SAMPLE_TEXT)
    instruct = voice_instruct.strip() or GENRE_PROMPTS.get(genre, "")
    lang     = _resolve_language(language)
    device   = _resolve_device(log_cb)

    if progress_cb:
        progress_cb(5.0)

    tts = _get_design_model(device, log_cb)

    if cancelled and cancelled():
        return None

    if log_cb:
        log_cb("Voice Anchor: Generating voice reference ...")
    if progress_cb:
        progress_cb(35.0)

    streamer = _TokenCountStreamer(
        log_cb=log_cb,
        progress_cb=progress_cb,
        estimated_tokens=_estimate_tokens(sample),
        start_pct=35.0,
        end_pct=80.0,
    )

    wavs, sr = tts.generate_voice_design(
        text=sample,
        instruct=instruct,
        language=lang,
        streamer=streamer,
    )

    # Do NOT del / unload — keep model warm for the next Generate click.

    if progress_cb:
        progress_cb(80.0)

    output_path = VOICE_ANCHORS_DIR / f"anchor_{genre}.wav"
    txt_path    = VOICE_ANCHORS_DIR / f"anchor_{genre}.txt"

    sf.write(str(output_path), wavs[0], sr)
    txt_path.write_text(sample, encoding="utf-8")

    if log_cb:
        log_cb(f"Voice Anchor: Saved {output_path.name} ({len(wavs[0]) / sr:.1f}s)")
    if progress_cb:
        progress_cb(100.0)

    return output_path


_LANG_CODE_TO_NAME: dict[str, str] = {
    "zh": "chinese", "en": "english", "fr": "french", "de": "german",
    "it": "italian", "ja": "japanese", "ko": "korean", "pt": "portuguese",
    "ru": "russian", "es": "spanish",
}


def _resolve_language(lang: str) -> str:
    lower = lang.lower().strip()
    if lower in _LANG_CODE_TO_NAME.values() or lower == "auto":
        return lower
    code = lower.split("-")[0].split("_")[0]
    return _LANG_CODE_TO_NAME.get(code, "auto")


def _resolve_device(log_cb: Callable[[str], None] | None = None) -> str:
    import torch
    wanted = TTS_DEVICE.lower()
    if wanted.startswith("cuda"):
        if not torch.cuda.is_available():
            if log_cb:
                log_cb("TTS: CUDA requested but not available — falling back to CPU.")
            return "cpu"
        return wanted
    return "cpu"


# ── Qwen3-TTS-Base clone wrapper ─────────────────────────────────────────────

class _QwenTTSCloneWrapper:
    """Uses Qwen3-TTS-Base to clone the designed anchor voice for each chunk.

    Workflow (matches the official "Voice Design then Clone" recipe):
      1. Load Qwen3-TTS-12Hz-1.7B-Base.
      2. Build a reusable voice_clone_prompt from the anchor WAV + transcript.
      3. Call generate_voice_clone() for every TTS chunk, reusing the prompt
         so audio features are extracted only once per audiobook run.
    """

    def __init__(
        self,
        anchor_path: Path | None,
        anchor_text: str,
        log_cb: Callable[[str], None] | None = None,
    ) -> None:
        import torch
        from qwen_tts import Qwen3TTSModel

        self._log    = log_cb
        self._device = _resolve_device(log_cb)

        if log_cb:
            log_cb(f"TTS: Loading clone model {TTS_CLONE_MODEL} ...")

        import torch
        from qwen_tts import Qwen3TTSModel

        kwargs: dict = {
            "device_map": self._device,
            "dtype": torch.bfloat16 if self._device != "cpu" else torch.float32,
        }
        attn = _best_attn_impl(self._device)
        if attn:
            kwargs["attn_implementation"] = attn

        self._model = Qwen3TTSModel.from_pretrained(TTS_CLONE_MODEL, **kwargs)

        if anchor_path is None or not anchor_path.exists():
            raise RuntimeError(
                "qwen_tts_clone backend requires a voice anchor WAV. "
                "Use the Voice Designer to create one first."
            )

        if log_cb:
            log_cb("TTS: Building reusable voice-clone prompt from anchor ...")

        self._voice_clone_prompt = self._model.create_voice_clone_prompt(
            ref_audio=str(anchor_path),
            ref_text=anchor_text,
            x_vector_only_mode=False,
        )

        if log_cb:
            log_cb("TTS: Voice-clone prompt ready — anchor features cached.")

    def synthesise(
        self,
        text: str,
        cancelled: Callable[[], bool] | None = None,
        language: str = "english",
    ) -> tuple[np.ndarray, int]:
        """Synthesise *text* and return (waveform_float32, sample_rate)."""
        if cancelled and cancelled():
            raise RuntimeError("generation cancelled")

        if self._log:
            self._log(f"TTS: Synthesising {len(text)} chars ...")

        streamer = _TokenCountStreamer(
            log_cb=self._log,
            estimated_tokens=_estimate_tokens(text),
        )

        t0 = time.time()
        wavs, sr = self._model.generate_voice_clone(
            text=text,
            language=language,
            voice_clone_prompt=self._voice_clone_prompt,
            streamer=streamer,
        )
        elapsed = time.time() - t0

        wav = np.asarray(wavs[0], dtype=np.float32)
        if wav.ndim > 1:
            wav = wav.mean(axis=1)

        if self._log:
            dur = len(wav) / sr
            self._log(
                f"TTS: {dur:.1f}s audio in {elapsed:.1f}s "
                f"(RTF {elapsed / max(dur, 0.001):.2f}x)"
            )

        return wav, sr


# ── Fish Speech s2.cpp wrapper ────────────────────────────────────────────────

class _FishSpeechCppWrapper:
    """Calls s2.exe as a subprocess for each chunk, cloning the anchor voice."""

    def __init__(
        self,
        anchor_path: Path | None,
        anchor_text: str,
        log_cb: Callable[[str], None] | None = None,
    ) -> None:
        self._anchor      = anchor_path
        self._anchor_text = anchor_text
        self._log         = log_cb
        self._exe         = Path(FISH_SPEECH_CPP_EXE)
        self._model       = Path(FISH_SPEECH_CPP_MODEL)
        self._tokenizer   = Path(FISH_SPEECH_CPP_TOKENIZER)
        self._vulkan      = FISH_SPEECH_CPP_VULKAN

        # Validate paths once at construction time.
        if not self._exe.exists():
            raise RuntimeError(
                f"s2.exe not found: {self._exe}\n"
                "Build with: cd D:/GIT/s2.cpp && cmake --build build --config Release"
            )
        if not self._model.exists():
            raise RuntimeError(f"GGUF model not found: {self._model}")
        if not self._tokenizer.exists():
            raise RuntimeError(f"tokenizer.json not found: {self._tokenizer}")

    def synthesise(
        self,
        text: str,
        cancelled: Callable[[], bool] | None = None,
    ) -> tuple[np.ndarray, int]:
        """Synthesise *text* and return (waveform_float32, sample_rate)."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
            out_path = Path(fh.name)
        try:
            _s2cpp_synthesise(
                text=text,
                out_path=out_path,
                anchor_path=self._anchor,
                anchor_text=self._anchor_text,
                log_cb=self._log,
                vulkan=self._vulkan,
            )
            if cancelled and cancelled():
                raise RuntimeError("generation cancelled")
            wav, sr = sf.read(str(out_path), dtype="float32")
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
            return wav, sr
        finally:
            out_path.unlink(missing_ok=True)


# ── s2.cpp low-level helpers ──────────────────────────────────────────────────

def _s2cpp_env() -> dict[str, str]:
    exe = Path(FISH_SPEECH_CPP_EXE)
    env = os.environ.copy()
    exe_dir = exe.parent
    bin_dir = exe_dir.parent / "bin" / "Release"
    extra = [str(exe_dir)] + ([str(bin_dir)] if bin_dir.exists() else [])
    env["PATH"] = os.pathsep.join(extra) + os.pathsep + env.get("PATH", "")
    return env


def _s2cpp_synthesise(
    text: str,
    out_path: Path,
    anchor_path: Path | None,
    anchor_text: str,
    log_cb: Callable[[str], None] | None = None,
    vulkan: int | None = None,
) -> None:
    """Run s2.exe synchronously and write output to *out_path*."""
    exe       = Path(FISH_SPEECH_CPP_EXE)
    model     = Path(FISH_SPEECH_CPP_MODEL)
    tokenizer = Path(FISH_SPEECH_CPP_TOKENIZER)
    if vulkan is None:
        vulkan = FISH_SPEECH_CPP_VULKAN

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(exe), "-m", str(model), "-t", str(tokenizer), "-text", text, "-o", str(out_path)]
    if vulkan >= 0:
        cmd += ["-v", str(vulkan)]
    if anchor_path is not None and anchor_path.exists() and anchor_text.strip():
        cmd += ["-pa", str(anchor_path), "-pt", anchor_text.strip()]

    if log_cb:
        log_cb(f"TTS: Synthesising {len(text)} chars ...")

    t0 = time.time()
    result = subprocess.run(cmd, env=_s2cpp_env(), capture_output=True, text=True)
    elapsed = time.time() - t0

    if result.returncode != 0:
        raise RuntimeError(
            f"s2.exe exited {result.returncode}: {result.stderr.strip() or result.stdout.strip()}"
        )

    if log_cb:
        try:
            info = sf.info(str(out_path))
            dur  = info.frames / info.samplerate
            log_cb(f"TTS: {dur:.1f}s audio in {elapsed:.1f}s (RTF {elapsed / max(dur, 0.001):.2f}x)")
        except Exception:
            log_cb(f"TTS: Done in {elapsed:.1f}s")


def _load_anchor_text(anchor_path: Path) -> str:
    """Return the transcript sidecar (.txt) for *anchor_path*, or empty string."""
    txt = anchor_path.with_suffix(".txt")
    if txt.exists():
        return txt.read_text(encoding="utf-8").strip()
    return ""


# ── Shared helpers ────────────────────────────────────────────────────────────

def _chapter_title_text(index: int, title: str, subdivision_type: str) -> str:
    label = f"{subdivision_type} {index}"
    return f"{label} - {title}" if title.strip() else label


def _normalize_rms(wav: np.ndarray, target_rms: float = 0.08) -> np.ndarray:
    rms = float(np.sqrt(np.mean(wav ** 2)))
    if rms < 1e-6:
        return wav
    return np.clip(wav * (target_rms / rms), -1.0, 1.0)


def _resample_if_needed(wav: np.ndarray, src_sr: int, target_sr: int) -> np.ndarray:
    """Linear-interpolation resample when src_sr != target_sr (numpy only)."""
    if src_sr == target_sr or len(wav) == 0:
        return wav
    target_len = max(1, int(round(len(wav) * target_sr / src_sr)))
    return np.interp(
        np.linspace(0.0, len(wav) - 1, target_len),
        np.arange(len(wav)),
        wav,
    ).astype(np.float32)


def _merge_and_save(
    chunk_wavs: list[tuple[object, int]],
    output: Path,
    log_cb: Callable[[str], None] | None = None,
    pauses: list[float] | None = None,
) -> None:
    sr = chunk_wavs[0][1]
    parts: list[np.ndarray] = []
    for i, (wav, chunk_sr) in enumerate(chunk_wavs):
        audio = _normalize_rms(_resample_if_needed(np.asarray(wav, dtype=np.float32), chunk_sr, sr))
        parts.append(audio)
        if i < len(chunk_wavs) - 1:
            pause_s = pauses[i] if pauses and i < len(pauses) else _SILENCE_CHUNK_S
            parts.append(np.zeros(int(pause_s * sr), dtype=np.float32))

    combined = np.concatenate(parts)
    sf.write(str(output), combined, sr)
    if log_cb:
        log_cb(f"TTS: Saved -> {output.name} ({len(combined) / sr:.1f}s)")


def _to_mp3(
    audio: np.ndarray,
    sr: int,
    wav_path: Path,
    log_cb: Callable[[str], None] | None = None,
) -> None:
    try:
        import lameenc
        pcm = (audio * 32767).clip(-32768, 32767).astype(np.int16)
        enc = lameenc.Encoder()
        enc.set_bit_rate(192)
        enc.set_in_sample_rate(sr)
        enc.set_channels(1)
        enc.set_quality(2)
        mp3_data = enc.encode(pcm.tobytes()) + enc.flush()
        mp3_path = wav_path.with_suffix(".mp3")
        mp3_path.write_bytes(mp3_data)
        if log_cb:
            log_cb(f"TTS: MP3 saved -> {mp3_path.name}")
    except Exception as exc:
        if log_cb:
            log_cb(f"TTS: MP3 encoding failed ({exc})")


def _merge_chapters(
    chapter_paths: list[Path],
    output: Path,
    log_cb: Callable[[str], None] | None = None,
) -> None:
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
        data = _resample_if_needed(data, file_sr, sr)
        parts.append(data)
        if i < len(chapter_paths) - 1:
            parts.append(np.zeros(int(3.0 * sr), dtype=np.float32))

    combined = np.concatenate(parts)
    sf.write(str(output), combined, sr)
    if log_cb:
        m, s = divmod(int(len(combined) / sr), 60)
        log_cb(f"TTS: Full audiobook saved -> {output.name} ({m}m {s}s)")
    _to_mp3(combined, sr, output, log_cb)


def _safe_filename(name: str, max_len: int = 60) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:max_len]
