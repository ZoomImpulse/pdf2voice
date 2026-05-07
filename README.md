# pdf2voice

A self-hosted PDF-to-audiobook converter with a PyQt6 desktop UI. Converts PDF documents into high-quality audiobooks using local LLMs and advanced text-to-speech — no cloud services required.

## Features

- **Smart PDF extraction** — Page-by-page extraction via PyMuPDF4LLM; uses embedded PDF bookmarks for reliable chapter detection, with LLM-parsed text TOC or heading-based fallback
- **LLM structuring** — Detects language, genre, title, and chapter boundaries; rewrites content for audio (lists → prose, visual references removed)
- **Two TTS backends** — Fish Speech S2 Pro via native binary (`fish_speech_cpp`) or Qwen3-TTS clone (`qwen_tts_clone`)
- **Voice Designer** — 10 built-in genre voice templates (novel, thriller, nonfiction, biography, selfhelp, philosophy, technical, history, children, poetry); customize 12 voice parameters; AI-assisted fill; live playback
- **Session resume** — Per-chunk WAV persistence; interrupted runs pick up from the last completed chunk
- **Chapter editing** — Inline preview, edit, and re-chunk any chapter before or after generation
- **Per-chapter regeneration** — Re-synthesize individual chapters without re-running the full pipeline
- **Self-bootstrapping** — `python main.py` creates the venv, detects CUDA, installs the correct PyTorch/torchaudio/fish-speech build automatically

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai/) running locally (`ollama serve`) — required for structuring and adaptation
- NVIDIA GPU with 8 GB+ VRAM (recommended); CPU fallback supported
- CUDA 11.8+ (auto-detected; PyTorch wheel selected accordingly)
- ~20 GB disk space for models and output

## Quick Start

```bash
git clone https://github.com/ZoomImpulse/pdf2voice.git
cd pdf2voice
python main.py your_book.pdf
```

On first run the bootstrapper will:

1. Create `.venv`
2. Detect your CUDA version and install matching PyTorch + torchaudio
3. Install fish-speech from GitHub
4. Install all other dependencies from `requirements.txt`
5. Launch the app

Subsequent runs skip completed steps via sentinel files in `.venv/`.

Pull the default LLM if you haven't already:

```bash
ollama pull qwen3:8b
```

## TTS Backends

### fish_speech_cpp (default)

Uses the [s2.cpp](https://github.com/fishaudio/s2.cpp) native binary with a GGUF-quantised Fish Speech S2 Pro model. Faster inference via Vulkan GPU acceleration.

**Setup:**
1. Build `s2.cpp` and point `FISH_SPEECH_CPP_EXE` to the resulting `s2.exe`
2. Open **Settings → S2 Pro checkpoint → Download (~5.6 GB)** to fetch the GGUF model and tokenizer from Hugging Face — paths are saved to `.env` automatically

### qwen_tts_clone

Pure-Python backend using Qwen3-TTS. No external binary required; models download from Hugging Face on first use. Slower on CPU but no extra setup needed.

Switch backends in Settings or set `TTS_BACKEND=qwen_tts_clone` in `.env`.

## Configuration

All settings are managed via the **Settings dialog** (gear icon) and persisted to `.env`. The full reference:

```env
# ── LLM ──────────────────────────────────────────────────────────────────────
OLLAMA_URL=http://localhost:11434
LLM_MODEL=qwen3:8b
LLM_CTX=16384               # token context window; keep below GPU VRAM headroom

# ── TTS ───────────────────────────────────────────────────────────────────────
TTS_BACKEND=fish_speech_cpp  # "fish_speech_cpp" | "qwen_tts_clone"
TTS_DEVICE=cuda              # "cuda" | "cpu" (VoiceDesign model)
TTS_CHUNK_SIZE=3000          # characters per TTS synthesis chunk
TTS_SEED=                    # optional; blank = random (reproducible voice)

# Qwen3-TTS models (used by both backends for voice design)
TTS_DESIGN_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
TTS_CLONE_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-Base    # qwen_tts_clone only

# ── Fish Speech S2 Pro (fish_speech_cpp backend) ──────────────────────────────
FISH_SPEECH_CPP_EXE=D:/GIT/s2.cpp/build/Release/s2.exe
FISH_SPEECH_CPP_MODEL=checkpoints/s2-pro-gguf/s2-pro-q8_0.gguf
FISH_SPEECH_CPP_TOKENIZER=checkpoints/s2-pro-gguf/tokenizer.json
FISH_SPEECH_CPP_VULKAN=0     # Vulkan GPU index; -1 = CPU only

# ── Voice ──────────────────────────────────────────────────────────────────────
TTS_GENDER=female            # "female" | "male" (injected into voice instruction)
TTS_VOICE_INSTRUCT=Speak as a professional audiobook narrator...
TTS_SPEAKER=                 # optional speaker name (CustomVoice)
TTS_REF_AUDIO=               # optional reference audio path for cloning
TTS_REF_TEXT=                # transcript of TTS_REF_AUDIO

# ── Output ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR=./output

# ── Adaptation ─────────────────────────────────────────────────────────────────
ADAPTATION_ENABLED=true
ADAPTATION_PROVIDER=ollama   # "ollama" | "openrouter"
OPENROUTER_API_KEY=          # required if ADAPTATION_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-haiku-4-5
```

## Pipeline

```
PDF
 │
 ▼ Extraction      pymupdf4llm — page-by-page Markdown; PDF bookmarks → chapter boundaries
 │
 ▼ Structuring     text cleaning, abbreviation expansion, chapter splitting, TTS chunking;
 │                 LLM detects language/genre/metadata; merges suspect over-splits
 │
 ▼ Adaptation      LLM rewrites chunks for audio (optional); lists → prose, visual refs removed
 │
 ▼ TTS Generation  Phase 1: VoiceDesign model generates anchor WAV from genre spec
                   Phase 2: Clone backend synthesises all chunks using the anchor
                   Output: per-chapter WAV files with silence pauses between chunks
```

Adaptation can be disabled (`ADAPTATION_ENABLED=false`) for faster processing or when the source text is already clean prose.

## Voice Designer

Open via the **Voices** button. Lets you customise the narrator voice for each genre across 12 parameters: gender, pitch, speed, volume, age, clarity, fluency, accent, texture, emotion, tone, and personality.

- Select a genre to load its built-in template
- Edit any field manually or use **AI Fill** to let the LLM populate the form from a free-text description
- **Generate** synthesises a short sample with the current spec
- **Use** saves the anchor and sets it as the active voice for that genre

Genre anchors are saved to `output/sessions/voice_anchors/` and reused across sessions.

## Project Structure

```
pdf2voice/
├── main.py                        # Entry point + bootstrapper
├── requirements.txt
├── src/
│   ├── app.py                     # Main PyQt6 application window
│   ├── config.py                  # All settings and genre voice specs
│   ├── workers.py                 # QThread workers (pipeline, regen, voice design)
│   ├── pipeline/
│   │   ├── extractor.py           # PDF → Markdown, TOC extraction
│   │   ├── preprocessor.py        # Text cleaning, chapter splitting, chunking
│   │   ├── structurer.py          # LLM metadata detection, StructuredBook
│   │   ├── adapter.py             # LLM audiobook adaptation
│   │   ├── tts_engine.py          # Voice design + clone TTS generation
│   │   └── session.py             # Session persistence and resume logic
│   └── widgets/
│       ├── info_bar.py            # PDF selector + config summary
│       ├── pipeline_section.py    # Collapsible stage progress cards
│       ├── chapter_section.py     # Chapter list with inline preview/edit
│       ├── log_panel.py           # Timestamped activity log
│       ├── settings_dialog.py     # Full .env settings UI + S2 Pro download
│       └── voice_designer_dialog.py  # Genre voice template editor
├── checkpoints/                   # Downloaded model checkpoints (git-ignored)
└── output/                        # Generated audiobooks (git-ignored)
```

## Troubleshooting

**Ollama not connecting** — ensure `ollama serve` is running and `OLLAMA_URL` is correct.

**TTS very slow** — check `TTS_DEVICE=cuda`; confirm PyTorch sees your GPU (`python -c "import torch; print(torch.cuda.is_available())"`).

**fish_speech_cpp not found** — set `FISH_SPEECH_CPP_EXE` in Settings or `.env` to the full path of your `s2.exe` build.

**S2 Pro checkpoint missing** — open Settings, switch backend to `fish_speech_cpp`, and click **Download (~5.6 GB)**.

**CUDA build mismatch** — delete `.venv/.torch_build` and re-run `python main.py` to force a clean PyTorch reinstall.

**fish-speech reinstall needed** — delete `.venv/.fish_speech_build` and re-run `python main.py`.

## Acknowledgements

- [Ollama](https://ollama.ai/) — local LLM runtime
- [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base) — voice synthesis models
- [Fish Speech / s2.cpp](https://github.com/fishaudio/s2.cpp) — GGUF-native TTS inference
- [PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm) — PDF extraction
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — desktop UI framework
