"""Dark QSS stylesheet for pdf2voice."""

DARK_STYLESHEET = """
/* ── Global ──────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0f0f13;
    color: #e2e8f0;
    font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
    font-size: 13px;
}

QLabel {
    background: transparent;
}

QSplitter::handle {
    background: #1e1e2e;
}
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }

/* ── Header bar ──────────────────────────────────────────────────── */
QFrame#header-bar {
    background-color: #0a0a10;
    border-bottom: 1px solid #1e1e2e;
}

QLabel#app-title {
    font-size: 18px;
    font-weight: 700;
    color: #a78bfa;
    letter-spacing: 0.5px;
}

QPushButton#header-btn {
    background: transparent;
    border: 1px solid #2e2e3e;
    border-radius: 6px;
    padding: 6px 14px;
    color: #94a3b8;
    font-size: 12px;
}
QPushButton#header-btn:hover {
    border-color: #7c3aed;
    color: #a78bfa;
    background: #1e1e2e;
}

/* ── Structural panels ───────────────────────────────────────────── */
QFrame#left-panel {
    background: #0f0f13;
    border-right: 1px solid #1e1e2e;
}
QFrame#center-panel {
    background: #0f0f13;
}
QFrame#footer-bar {
    background: #0a0a10;
    border-top: 1px solid #1e1e2e;
}

/* ── Group boxes ─────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #1e1e2e;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: 600;
    color: #64748b;
    font-size: 11px;
    letter-spacing: 0.8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #64748b;
}

/* ── Path input ──────────────────────────────────────────────────── */
QLineEdit#path-edit {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    border-radius: 6px;
    padding: 7px 10px;
    color: #e2e8f0;
    selection-background-color: #7c3aed;
}
QLineEdit#path-edit:focus {
    border-color: #7c3aed;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton#browse-btn {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    border-radius: 6px;
    padding: 7px 12px;
    color: #94a3b8;
}
QPushButton#browse-btn:hover {
    background: #1e1e2e;
    border-color: #7c3aed;
    color: #e2e8f0;
}

/* ── Voice gender pill toggle ────────────────────────────────────── */
QPushButton#voice-pill-left,
QPushButton#voice-pill-right {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    color: #64748b;
    font-size: 13px;
    font-weight: 500;
    padding: 0 16px;
}
QPushButton#voice-pill-left  { border-radius: 0; border-top-left-radius: 8px; border-bottom-left-radius: 8px; border-right: none; }
QPushButton#voice-pill-right { border-radius: 0; border-top-right-radius: 8px; border-bottom-right-radius: 8px; }

QPushButton#voice-pill-left:hover,
QPushButton#voice-pill-right:hover {
    background: #1e1e2e;
    color: #94a3b8;
}

QPushButton#voice-pill-left-active {
    background: #2e1f5e;
    border: 1px solid #7c3aed;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: none;
    color: #c4b5fd;
    font-size: 13px;
    font-weight: 600;
    padding: 0 16px;
}
QPushButton#voice-pill-right-active {
    background: #2e1f5e;
    border: 1px solid #7c3aed;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    color: #c4b5fd;
    font-size: 13px;
    font-weight: 600;
    padding: 0 16px;
}

QPushButton#voice-pill-left:disabled,
QPushButton#voice-pill-right:disabled,
QPushButton#voice-pill-left-active:disabled,
QPushButton#voice-pill-right-active:disabled {
    opacity: 0.4;
}

/* ── Settings labels ─────────────────────────────────────────────── */
QLabel#settings-key {
    color: #475569;
    font-size: 11px;
}
QLabel#settings-val {
    color: #a78bfa;
    font-size: 11px;
}

/* ── Panel section titles ────────────────────────────────────────── */
QLabel#panel-title {
    font-weight: 700;
    font-size: 11px;
    color: #64748b;
    letter-spacing: 1px;
    padding-bottom: 4px;
}

/* ── Pipeline card ───────────────────────────────────────────────── */
QWidget#pipeline-panel {
    background: #1a1a24;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}

/* Step dots */
QLabel#step-dot-pending {
    background: #2a2a3e;
    border: 2px solid #3a3a5e;
    border-radius: 14px;
    color: #475569;
    font-size: 11px;
    font-weight: 700;
}
QLabel#step-dot-running {
    background: #2e1f5e;
    border: 2px solid #7c3aed;
    border-radius: 14px;
    color: #a78bfa;
    font-size: 11px;
    font-weight: 700;
}
QLabel#step-dot-done {
    background: #14532d;
    border: 2px solid #22c55e;
    border-radius: 14px;
    color: #22c55e;
    font-size: 11px;
    font-weight: 700;
}
QLabel#step-dot-error {
    background: #450a0a;
    border: 2px solid #ef4444;
    border-radius: 14px;
    color: #ef4444;
    font-size: 11px;
    font-weight: 700;
}

/* Connector lines between dots */
QLabel#step-sep {
    background: #2a2a3e;
    margin-top: 12px;
}

QLabel#step-label {
    color: #475569;
    font-size: 10px;
    max-width: 80px;
}

/* Single animated progress bar */
QProgressBar#pipeline-bar {
    background: #2a2a3e;
    border: none;
    border-radius: 4px;
}
QProgressBar#pipeline-bar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #a78bfa);
    border-radius: 4px;
}

QLabel#pipeline-spinner {
    color: #a78bfa;
    font-size: 15px;
}

QLabel#pipeline-stage-lbl {
    color: #64748b;
    font-size: 11px;
}

/* ── Chapter list ────────────────────────────────────────────────── */
QWidget#chapter-panel {
    background: #1a1a24;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}

QFrame#side-panel-header {
    background: transparent;
}

QLabel#side-panel-title {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

QFrame#panel-sep {
    background: #1e1e2e;
}

QWidget#panel-scroll-content {
    background: #1a1a24;
}

QFrame#chapter-card {
    background: #111118;
    border-radius: 0px;
    border-left: none;
}

QFrame#card-dot-pending { background: #2d3748; border-radius: 4px; }
QFrame#card-dot-running { background: #a78bfa; border-radius: 4px; }
QFrame#card-dot-done    { background: #22c55e; border-radius: 4px; }
QFrame#card-dot-error   { background: #ef4444; border-radius: 4px; }

QLabel#card-num {
    color: #334155;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel#card-title {
    color: #64748b;
    font-size: 12px;
}

/* ── Preview panel ───────────────────────────────────────────────── */
QWidget#preview-panel {
    background: #1a1a24;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}

QWidget#preview-content {
    background: #1a1a24;
}

QLabel#preview-placeholder {
    color: #2d3748;
    font-size: 13px;
    padding: 20px;
}

QLabel#preview-chapter-title {
    color: #a78bfa;
    font-size: 16px;
    font-weight: 700;
}

QLabel#preview-meta {
    color: #334155;
    font-size: 11px;
}

QFrame#preview-announcement {
    background: transparent;
    border: none;
    border-left: 2px solid #f59e0b;
    border-radius: 0;
}

QLabel#preview-ann-header {
    color: #d97706;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

QLabel#preview-ann-text {
    color: #fcd34d;
    font-style: italic;
    font-size: 12px;
}

QLabel#preview-section-header {
    color: #334155;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

QFrame#preview-chunk-card {
    background: transparent;
    border: none;
    border-left: 2px solid #1e1e2e;
    border-radius: 0;
}

QLabel#chunk-badge {
    background: #2e1f5e;
    color: #a78bfa;
    font-size: 11px;
    font-weight: 700;
    border-radius: 11px;
}

QLabel#chunk-chars {
    color: #2d3748;
    font-size: 10px;
    font-family: monospace;
}

QLabel#chunk-body {
    color: #64748b;
    font-size: 12px;
    padding-left: 4px;
}

/* ── Log card ────────────────────────────────────────────────────── */
QWidget#log-panel {
    background: #1a1a24;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}

QTextEdit#log-text {
    background: transparent;
    border: none;
    color: #e2e8f0;
    font-size: 12px;
    selection-background-color: #7c3aed;
}

/* ── Footer action buttons ───────────────────────────────────────── */
QPushButton#btn-start {
    background: #15803d;
    border: 1px solid #16a34a;
    border-radius: 6px;
    padding: 0 20px;
    color: #f0fdf4;
    font-weight: 600;
    min-width: 90px;
}
QPushButton#btn-start:hover    { background: #16a34a; }
QPushButton#btn-start:disabled { background: #1a2e1a; border-color: #1a2e1a; color: #3a5a3a; }

QPushButton#btn-confirm {
    background: #1d4ed8;
    border: 1px solid #2563eb;
    border-radius: 6px;
    padding: 0 20px;
    color: #eff6ff;
    font-weight: 600;
    min-width: 170px;
}
QPushButton#btn-confirm:hover    { background: #2563eb; }
QPushButton#btn-confirm:disabled { background: #1a1e2e; border-color: #1a1e2e; color: #344060; }

QPushButton#btn-pause {
    background: #92400e;
    border: 1px solid #b45309;
    border-radius: 6px;
    padding: 0 20px;
    color: #fef3c7;
    font-weight: 600;
    min-width: 90px;
}
QPushButton#btn-pause:hover    { background: #b45309; }
QPushButton#btn-pause:disabled { background: #1a1810; border-color: #1a1810; color: #403020; }

QPushButton#btn-cancel {
    background: #7f1d1d;
    border: 1px solid #991b1b;
    border-radius: 6px;
    padding: 0 20px;
    color: #fef2f2;
    font-weight: 600;
    min-width: 90px;
}
QPushButton#btn-cancel:hover    { background: #991b1b; }
QPushButton#btn-cancel:disabled { background: #1a1010; border-color: #1a1010; color: #402020; }

/* ── Status label ────────────────────────────────────────────────── */
QLabel#status-label {
    color: #475569;
    font-size: 12px;
}

/* ── Inline confirmation banner ──────────────────────────────────── */
QFrame#confirm-bar {
    background: #1a1f2e;
    border: 1px solid #2e3a5a;
    border-left: 3px solid #7c3aed;
    border-radius: 8px;
}

QLabel#confirm-bar-icon {
    font-size: 16px;
}

QLabel#confirm-bar-msg {
    color: #94a3b8;
    font-size: 12px;
}

QPushButton#btn-generate {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #9333ea);
    border: none;
    border-radius: 6px;
    padding: 0 20px;
    color: #f5f3ff;
    font-weight: 700;
    font-size: 13px;
    min-width: 150px;
}
QPushButton#btn-generate:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6d28d9, stop:1 #7c3aed);
}
QPushButton#btn-generate:pressed {
    background: #5b21b6;
}

/* ── Edit chapter button (preview header) ────────────────────────── */
QPushButton#btn-edit-chapter {
    background: transparent;
    border: 1px solid #2e2e3e;
    border-radius: 5px;
    padding: 3px 10px;
    color: #94a3b8;
    font-size: 11px;
}
QPushButton#btn-edit-chapter:hover {
    border-color: #7c3aed;
    color: #a78bfa;
}

/* ── Chapter text editor ─────────────────────────────────────────── */
QTextEdit#chapter-text-edit {
    background: #111118;
    border: 1px solid #2e3a5a;
    border-radius: 6px;
    padding: 10px;
    color: #e2e8f0;
    font-size: 13px;
    selection-background-color: #7c3aed;
}
QTextEdit#chapter-text-edit:focus {
    border-color: #7c3aed;
}

/* ── Edit mode action buttons ────────────────────────────────────── */
QPushButton#btn-edit-save {
    background: #1d4ed8;
    border: 1px solid #2563eb;
    border-radius: 6px;
    padding: 5px 16px;
    color: #eff6ff;
    font-weight: 600;
}
QPushButton#btn-edit-save:hover { background: #2563eb; }

QPushButton#btn-edit-cancel {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    border-radius: 6px;
    padding: 5px 14px;
    color: #94a3b8;
}
QPushButton#btn-edit-cancel:hover {
    border-color: #7c3aed;
    color: #e2e8f0;
}

/* ── Regenerate button on chapter card ───────────────────────────── */
QPushButton#btn-regen {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    border-radius: 4px;
    color: #64748b;
    font-size: 13px;
    font-weight: 700;
}
QPushButton#btn-regen:hover {
    background: #14532d;
    border-color: #16a34a;
    color: #22c55e;
}
QPushButton#btn-regen:disabled {
    color: #2d3748;
    border-color: #1e1e2e;
}

/* ── Settings dialog ─────────────────────────────────────────────── */
QDialog {
    background: #13131a;
}

QLineEdit#settings-input {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
    selection-background-color: #7c3aed;
}
QLineEdit#settings-input:focus {
    border-color: #7c3aed;
}
QLineEdit#settings-input:disabled {
    color: #334155;
    border-color: #1e1e2e;
    background: #111118;
}

QComboBox {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
}
QComboBox:disabled {
    color: #334155;
    background: #111118;
}
QComboBox QAbstractItemView {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    color: #e2e8f0;
    selection-background-color: #7c3aed;
}
QComboBox::drop-down { border: none; }

QCheckBox {
    color: #94a3b8;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #2e2e3e;
    border-radius: 4px;
    background: #1a1a24;
}
QCheckBox::indicator:checked {
    background: #7c3aed;
    border-color: #7c3aed;
}

QLabel#settings-hint {
    color: #475569;
    font-size: 11px;
}

QLabel#settings-section {
    color: #7c3aed;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding-top: 18px;
    padding-bottom: 4px;
    border-bottom: 1px solid #2e2e3e;
}

QDialogButtonBox QPushButton {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    border-radius: 6px;
    padding: 6px 18px;
    color: #94a3b8;
    min-width: 70px;
}
QDialogButtonBox QPushButton:hover {
    border-color: #7c3aed;
    color: #e2e8f0;
}
QDialogButtonBox QPushButton[text="OK"] {
    background: #1d4ed8;
    border-color: #2563eb;
    color: #eff6ff;
    font-weight: 600;
}
QDialogButtonBox QPushButton[text="OK"]:hover {
    background: #2563eb;
}

/* ── Scrollbars ──────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2e2e3e;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover  { background: #7c3aed; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical      { height: 0; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical      { background: transparent; }

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border: none;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #2e2e3e;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #7c3aed; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal     { width: 0; }
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal     { background: transparent; }

/* ── Scrollable body ─────────────────────────────────────────────── */
QWidget#scroll-body {
    background: #0f0f13;
}

/* ── Info bar (top card row) ─────────────────────────────────────── */
QFrame#info-bar {
    background: transparent;
}

QFrame#info-card {
    background: #13131a;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}

QLabel#info-card-title {
    color: #475569;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

QLabel#info-card-meta {
    color: #64748b;
    font-size: 11px;
}

/* ── Section containers (pipeline + chapter) ─────────────────────── */
QFrame#pipeline-section,
QFrame#chapter-section {
    background: #13131a;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}

QFrame#section-header {
    background: transparent;
    border-radius: 10px;
}

QLabel#section-title {
    color: #475569;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.9px;
}

QPushButton#section-toggle-btn {
    background: transparent;
    border: 1px solid #2e2e3e;
    border-radius: 4px;
    color: #475569;
    font-size: 11px;
    font-weight: 700;
    padding: 0;
}
QPushButton#section-toggle-btn:hover {
    border-color: #7c3aed;
    color: #a78bfa;
}

/* ── Settings adaptation toggle ──────────────────────────────────── */
QPushButton#toggle-btn {
    background: #1a1a24;
    border: 1px solid #2e2e3e;
    border-radius: 12px;
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    min-width: 52px;
    max-width: 52px;
    padding: 4px 0;
}
QPushButton#toggle-btn:checked {
    background: #6d28d9;
    border-color: #7c3aed;
    color: #ffffff;
}
QPushButton#toggle-btn:hover {
    border-color: #7c3aed;
}
QPushButton#toggle-btn:checked:hover {
    background: #7c3aed;
}

QWidget#section-content {
    background: transparent;
}

/* ── Stage rows ──────────────────────────────────────────────────── */
QFrame#stage-row {
    background: transparent;
}

QFrame#stage-sep {
    background: #1a1a24;
}

QLabel#stage-name {
    color: #94a3b8;
    font-size: 13px;
    font-weight: 600;
}

QLabel#stage-desc {
    color: #334155;
    font-size: 12px;
}

QLabel#stage-detail {
    color: #64748b;
    font-size: 11px;
}

/* Stage status icons */
QFrame#stage-icon-pending { background: #2d3748; border-radius: 5px; }
QFrame#stage-icon-running { background: #a78bfa; border-radius: 5px; }
QFrame#stage-icon-done    { background: #22c55e; border-radius: 5px; }
QFrame#stage-icon-error   { background: #ef4444; border-radius: 5px; }

/* Stage state labels */
QLabel#stage-state-pending { color: #2d3748; font-size: 11px; }
QLabel#stage-state-running { color: #a78bfa; font-size: 11px; }
QLabel#stage-state-done    { color: #22c55e; font-size: 11px; }
QLabel#stage-state-error   { color: #ef4444; font-size: 11px; }

/* ── Expandable chapter cards ────────────────────────────────────── */
QFrame#exp-chapter-card {
    background: #13131a;
}

QFrame#exp-card-header {
    background: transparent;
}

QFrame#exp-card-header:hover {
    background: #17171f;
}

QFrame#exp-card-header-active {
    background: #160f2e;
}

QWidget#exp-card-content {
    background: #0f0f13;
}

QLabel#exp-icon {
    color: #334155;
    font-size: 11px;
}

QFrame#card-sep {
    background: #1a1a24;
}
"""
