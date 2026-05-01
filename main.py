#!/usr/bin/env python3
"""pdf2voice — PDF to Audiobook converter (self-hosted, terminal UI)

Usage:
    python main.py [PDF_PATH]
"""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
SENTINEL = VENV_DIR / ".req_hash"
TORCH_SENTINEL = VENV_DIR / ".torch_build"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _in_project_venv() -> bool:
    return Path(sys.prefix).resolve() == VENV_DIR.resolve()


def _req_hash() -> str:
    return hashlib.md5(REQUIREMENTS.read_bytes()).hexdigest()


def _needs_install() -> bool:
    return not SENTINEL.exists() or SENTINEL.read_text().strip() != _req_hash()


def _print(msg: str) -> None:
    print(f"\033[36m[pdf2voice]\033[0m {msg}", flush=True)


def _print_ok(msg: str) -> None:
    print(f"\033[32m[pdf2voice]\033[0m {msg}", flush=True)


def _print_warn(msg: str) -> None:
    print(f"\033[33m[pdf2voice]\033[0m {msg}", flush=True)


# ── CUDA detection ────────────────────────────────────────────────────────────

def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\[\?[0-9;]*[a-zA-Z]", "", text)


def _detect_cuda_version() -> str | None:
    """Return CUDA version string like '12.4', or None if no NVIDIA GPU found."""
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None
        clean = _strip_ansi(result.stdout)
        match = re.search(r"CUDA Version:\s*(\d+\.\d+)", clean)
        if match:
            return match.group(1)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _cuda_tag(cuda_ver: str) -> str:
    """Map detected CUDA version to the nearest available PyTorch wheel tag."""
    major, minor = (int(x) for x in cuda_ver.split(".")[:2])
    # CUDA 13.x and 12.6+ → cu126 (latest PyTorch CUDA build)
    if major >= 13 or (major == 12 and minor >= 6):
        return "cu126"
    if major == 12 and minor >= 4:
        return "cu124"
    if major == 12 and minor >= 1:
        return "cu121"
    return "cu118"  # CUDA 11.8 — lowest supported


def _install_torch(cuda_ver: str | None) -> str:
    """Uninstall existing torch and reinstall with the correct CUDA build."""
    # Uninstall first so pip doesn't skip reinstall when version matches
    subprocess.run(
        [str(_venv_python()), "-m", "pip", "uninstall", "torch", "-y"],
        capture_output=True,
    )

    if cuda_ver is None:
        _print_warn("Keine NVIDIA-GPU gefunden — installiere PyTorch (CPU).")
        subprocess.check_call([
            str(_venv_python()), "-m", "pip", "install", "--quiet", "torch",
        ])
        return "cpu"

    tag = _cuda_tag(cuda_ver)
    index_url = f"https://download.pytorch.org/whl/{tag}"
    _print(f"CUDA {cuda_ver} erkannt → installiere PyTorch ({tag}) ...")
    subprocess.check_call([
        str(_venv_python()), "-m", "pip", "install", "--quiet",
        "torch", "--index-url", index_url,
    ])
    _print_ok(f"PyTorch ({tag}) installiert.")
    return tag


def _torch_needs_reinstall(cuda_ver: str | None) -> bool:
    """True if torch is missing or was built for a different target (cpu vs cuda)."""
    if not TORCH_SENTINEL.exists():
        return True
    installed_tag = TORCH_SENTINEL.read_text().strip()
    wanted_tag = "cpu" if cuda_ver is None else _cuda_tag(cuda_ver)
    return installed_tag != wanted_tag


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def bootstrap() -> None:
    if not VENV_DIR.exists():
        _print("Erstelle virtuelle Umgebung (.venv) ...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        _print_ok("Virtuelle Umgebung erstellt.")

    subprocess.check_call([
        str(_venv_python()), "-m", "pip", "install", "--quiet", "--upgrade", "pip",
    ])

    cuda_ver = _detect_cuda_version()

    if _torch_needs_reinstall(cuda_ver):
        tag = _install_torch(cuda_ver)
        TORCH_SENTINEL.write_text(tag)
    else:
        _print(f"PyTorch ({TORCH_SENTINEL.read_text().strip()}) bereits installiert.")

    if _needs_install():
        _print("Installiere Abhängigkeiten aus requirements.txt ...")
        subprocess.check_call([
            str(_venv_python()), "-m", "pip", "install", "--quiet",
            "-r", str(REQUIREMENTS),
        ])
        SENTINEL.write_text(_req_hash())
        _print_ok("Abhängigkeiten bereit.")

    _print("Starte App ...")
    result = subprocess.run([str(_venv_python())] + sys.argv)
    sys.exit(result.returncode)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if not _in_project_venv():
        bootstrap()
        return

    from src.app import Pdf2VoiceApp
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = Pdf2VoiceApp(pdf_path=pdf_path)
    app.run()


if __name__ == "__main__":
    main()
