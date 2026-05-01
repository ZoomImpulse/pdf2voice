# pdf2voice 🎙️

A self-hosted PDF-to-audiobook converter with a beautiful terminal UI. Converts PDF documents into high-quality audiobooks using local LLMs and advanced text-to-speech technology.

## Features

- 📄 **Smart PDF Extraction** — Preserves heading structure and formatting using PyMuPDF4LLM
- 🤖 **Local LLM Processing** — Uses Ollama for cost-free, private text processing
- 🎵 **Advanced TTS** — Qwen3-TTS with voice design and cloning for natural-sounding narration
- 🎭 **Voice Customization** — Choose between male and female voices with tailored instructions
- 💻 **Terminal UI** — Clean, responsive interface built with Textual framework
- 📊 **Real-time Progress** — Live pipeline visualization and logging
- 🔧 **Configurable** — Customize models, voice styles, and processing parameters via `.env`

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai/) — Local LLM runtime (required)
- PyTorch (auto-installed)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ZoomImpulse/pdf2voice.git
   cd pdf2voice
   ```

2. **Run the app:**
   ```bash
   python main.py [PDF_PATH]
   ```
   The script automatically:
   - Creates a virtual environment
   - Installs dependencies
   - Launches the application

3. **Configure Ollama:**
   - Ensure Ollama is running (default: `http://localhost:11434`)
   - Pull the default model: `ollama pull qwen3:8b`

## Configuration

Create a `.env` file in the project root to customize settings:

```env
# Ollama LLM Server
OLLAMA_URL=http://localhost:11434
LLM_MODEL=qwen3:8b

# Text-to-Speech Models
TTS_DESIGN_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
TTS_BASE_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-Base

# Voice Settings
TTS_GENDER=female  # "female" | "male"
TTS_VOICE_INSTRUCT=Speak as a professional audiobook narrator...
```

## Usage

### Basic Usage
```bash
python main.py document.pdf
```

### Interactive Mode
The terminal UI provides:
- **Chapter List** — Navigate through extracted chapters
- **Pipeline Status** — Monitor processing stages (extraction → structuring → TTS)
- **Voice Selection** — Switch between male/female voices
- **Audio Output** — Preview and manage generated audio files

### Output
Generated audiobooks are saved to the `output/` directory as `.wav` files.

## Project Structure

```
pdf2voice/
├── main.py                 # Entry point and venv setup
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── src/
│   ├── app.py            # Textual UI application
│   ├── config.py         # Configuration management
│   ├── pipeline/         # Processing pipeline
│   │   ├── extractor.py  # PDF → Markdown extraction
│   │   ├── structurer.py # Text chunking and structuring
│   │   └── tts_engine.py # TTS generation
│   └── widgets/          # UI components
│       ├── chapter_list.py
│       ├── log_panel.py
│       └── pipeline_panel.py
└── output/              # Generated audiobooks
```

## Architecture

The processing pipeline follows a three-stage architecture:

1. **Extractor** — Converts PDF to structured Markdown
2. **Structurer** — Chunks text intelligently, processes with LLM
3. **TTS Engine** — Generates audio using voice design + base models

Voice design and cloning ensures consistent narration across all content chunks.

## Dependencies

- **textual** — Terminal UI framework
- **rich** — Terminal output formatting
- **pymupdf4llm** — PDF extraction with LLM awareness
- **ollama** — LLM client
- **qwen-tts** — Qwen text-to-speech models
- **soundfile** — Audio file handling
- **pydub** — Audio processing
- **python-dotenv** — Environment configuration

## Troubleshooting

### Ollama Connection Failed
- Ensure Ollama is running: `ollama serve`
- Check `OLLAMA_URL` in `.env` (default: `http://localhost:11434`)

### Model Download Issues
- Models are auto-downloaded on first use
- For manual download: `ollama pull qwen3:8b`

### Audio Generation Slow
- Check system resources (TTS is GPU-accelerated)
- Reduce LLM_MODEL size for faster processing

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

[Add your license here]

## Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM inference
- [Textual](https://textual.textualize.io/) for the terminal UI framework
- [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base) for voice synthesis
- [PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm) for intelligent PDF extraction
