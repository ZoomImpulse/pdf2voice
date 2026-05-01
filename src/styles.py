"""Dark QSS stylesheet for pdf2voice."""

DARK_STYLESHEET = """
/* ── Global ──────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0f0f13;
    color: #e2e8f0;
    font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
    font-size: 13px;
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

/* ── Radio buttons ───────────────────────────────────────────────── */
QRadioButton {
    color: #94a3b8;
    spacing: 8px;
    padding: 4px 0;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #2e2e3e;
    border-radius: 8px;
    background: #1a1a24;
}
QRadioButton::indicator:checked {
    background: #7c3aed;
    border-color: #7c3aed;
}
QRadioButton:checked { color: #e2e8f0; }

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

QLabel#stage-num {
    color: #475569;
    font-size: 11px;
    font-weight: 700;
}
QLabel#stage-name {
    color: #94a3b8;
    font-size: 12px;
}
QLabel#stage-status {
    color: #475569;
    font-size: 13px;
}
QLabel#stage-status-running { color: #a78bfa; }
QLabel#stage-status-done    { color: #22c55e; }
QLabel#stage-status-error   { color: #ef4444; }

QProgressBar#stage-bar {
    background: #2a2a3e;
    border: none;
    border-radius: 3px;
    max-height: 6px;
}
QProgressBar#stage-bar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #a78bfa);
    border-radius: 3px;
}

/* ── Chapter list ────────────────────────────────────────────────── */
QWidget#chapter-panel {
    background: #1a1a24;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}

QListWidget#chapter-list {
    background: transparent;
    border: none;
    outline: none;
    padding: 2px;
}
QListWidget#chapter-list::item {
    padding: 5px 8px;
    border-radius: 4px;
}
QListWidget#chapter-list::item:selected {
    background: #2e1f5e;
    color: #a78bfa;
}
QListWidget#chapter-list::item:hover:!selected {
    background: #1e1e2e;
}

/* ── Preview & Log cards ─────────────────────────────────────────── */
QWidget#preview-panel {
    background: #1a1a24;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}
QWidget#log-panel {
    background: #1a1a24;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
}

QTextEdit#preview-text, QTextEdit#log-text {
    background: transparent;
    border: none;
    color: #e2e8f0;
    font-size: 12px;
    line-height: 1.6;
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
"""
