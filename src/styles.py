"""Dark red QSS stylesheet for pdf2voice."""

DARK_STYLESHEET = """
/* ── Global ──────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #000000;
    color: #e2e8f0;
    font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
    font-size: 13px;
}

QLabel {
    background: transparent;
}

QSplitter::handle {
    background: #1e0000;
}
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }

/* ── Header bar ──────────────────────────────────────────────────── */
QFrame#header-bar {
    background-color: #050000;
    border-bottom: 1px solid #1e0000;
}

QLabel#app-title {
    font-size: 18px;
    font-weight: 700;
    color: #f87171;
    letter-spacing: 0.5px;
}

QPushButton#header-btn {
    background: transparent;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 6px 14px;
    color: #fca5a5;
    font-size: 12px;
}
QPushButton#header-btn:hover {
    border-color: #dc2626;
    color: #f87171;
    background: #1e0000;
}

/* ── Structural panels ───────────────────────────────────────────── */
QFrame#left-panel {
    background: #000000;
    border-right: 1px solid #1e0000;
}
QFrame#center-panel {
    background: #000000;
}
QFrame#footer-bar {
    background: #050000;
    border-top: 1px solid #1e0000;
}

/* ── Group boxes ─────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #1e0000;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: 600;
    color: #9f2020;
    font-size: 11px;
    letter-spacing: 0.8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #9f2020;
}

/* ── Path input ──────────────────────────────────────────────────── */
QLineEdit#path-edit {
    background: #0f0000;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 7px 10px;
    color: #e2e8f0;
    selection-background-color: #dc2626;
}
QLineEdit#path-edit:focus {
    border-color: #dc2626;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton#browse-btn {
    background: #0f0000;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 7px 12px;
    color: #fca5a5;
}
QPushButton#browse-btn:hover {
    background: #1e0000;
    border-color: #dc2626;
    color: #e2e8f0;
}

/* ── Voice gender pill toggle ────────────────────────────────────── */
QPushButton#voice-pill-left,
QPushButton#voice-pill-right {
    background: #0f0000;
    border: 1px solid #2a0000;
    color: #9f2020;
    font-size: 13px;
    font-weight: 500;
    padding: 0 16px;
}
QPushButton#voice-pill-left  { border-radius: 0; border-top-left-radius: 8px; border-bottom-left-radius: 8px; border-right: none; }
QPushButton#voice-pill-right { border-radius: 0; border-top-right-radius: 8px; border-bottom-right-radius: 8px; }

QPushButton#voice-pill-left:hover,
QPushButton#voice-pill-right:hover {
    background: #1e0000;
    color: #fca5a5;
}

QPushButton#voice-pill-left-active {
    background: #3b0000;
    border: 1px solid #dc2626;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: none;
    color: #fca5a5;
    font-size: 13px;
    font-weight: 600;
    padding: 0 16px;
}
QPushButton#voice-pill-right-active {
    background: #3b0000;
    border: 1px solid #dc2626;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    color: #fca5a5;
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
    color: #7f1d1d;
    font-size: 11px;
}
QLabel#settings-val {
    color: #f87171;
    font-size: 11px;
}

/* ── Panel section titles ────────────────────────────────────────── */
QLabel#panel-title {
    font-weight: 700;
    font-size: 11px;
    color: #9f2020;
    letter-spacing: 1px;
    padding-bottom: 4px;
}

/* ── Pipeline card ───────────────────────────────────────────────── */
QWidget#pipeline-panel {
    background: #0f0000;
    border: 1px solid #1e0000;
    border-radius: 10px;
}

/* Step dots */
QLabel#step-dot-pending {
    background: #1c0000;
    border: 2px solid #350000;
    border-radius: 14px;
    color: #7f1d1d;
    font-size: 11px;
    font-weight: 700;
}
QLabel#step-dot-running {
    background: #3b0000;
    border: 2px solid #dc2626;
    border-radius: 14px;
    color: #f87171;
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
    background: #1c0000;
    margin-top: 12px;
}

QLabel#step-label {
    color: #7f1d1d;
    font-size: 10px;
    max-width: 80px;
}

/* Single animated progress bar */
QProgressBar#pipeline-bar {
    background: #1c0000;
    border: none;
    border-radius: 4px;
}
QProgressBar#pipeline-bar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #dc2626, stop:1 #f87171);
    border-radius: 4px;
}

QLabel#pipeline-spinner {
    color: #f87171;
    font-size: 15px;
}

QLabel#pipeline-stage-lbl {
    color: #9f2020;
    font-size: 11px;
}

/* ── Chapter list ────────────────────────────────────────────────── */
QWidget#chapter-panel {
    background: #0f0000;
    border: 1px solid #1e0000;
    border-radius: 10px;
}

QFrame#side-panel-header {
    background: transparent;
}

QLabel#side-panel-title {
    color: #9f2020;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

QFrame#panel-sep {
    background: #1e0000;
}

QWidget#panel-scroll-content {
    background: #0f0000;
}

QFrame#chapter-card {
    background: #080000;
    border-radius: 0px;
    border-left: none;
}

QFrame#card-dot-pending { background: #250000; border-radius: 4px; }
QFrame#card-dot-running { background: #f87171; border-radius: 4px; }
QFrame#card-dot-done    { background: #22c55e; border-radius: 4px; }
QFrame#card-dot-error   { background: #ef4444; border-radius: 4px; }

QLabel#card-num {
    color: #4a0000;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel#card-title {
    color: #9f2020;
    font-size: 12px;
}

/* ── Preview panel ───────────────────────────────────────────────── */
QWidget#preview-panel {
    background: #0f0000;
    border: 1px solid #1e0000;
    border-radius: 10px;
}

QWidget#preview-content {
    background: #0f0000;
}

QLabel#preview-placeholder {
    color: #250000;
    font-size: 13px;
    padding: 20px;
}

QLabel#preview-chapter-title {
    color: #f87171;
    font-size: 16px;
    font-weight: 700;
}

QLabel#preview-meta {
    color: #4a0000;
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
    color: #4a0000;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

QFrame#preview-chunk-card {
    background: transparent;
    border: none;
    border-left: 2px solid #1e0000;
    border-radius: 0;
}

QLabel#chunk-badge {
    background: #3b0000;
    color: #f87171;
    font-size: 11px;
    font-weight: 700;
    border-radius: 11px;
}

QLabel#chunk-chars {
    color: #250000;
    font-size: 10px;
    font-family: monospace;
}

QLabel#chunk-body {
    color: #9f2020;
    font-size: 12px;
    padding-left: 4px;
}

/* ── Log card ────────────────────────────────────────────────────── */
QWidget#log-panel {
    background: #0f0000;
    border: 1px solid #1e0000;
    border-radius: 10px;
}

QTextEdit#log-text {
    background: transparent;
    border: none;
    color: #e2e8f0;
    font-size: 12px;
    selection-background-color: #dc2626;
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
    background: #991b1b;
    border: 1px solid #b91c1c;
    border-radius: 6px;
    padding: 0 20px;
    color: #fff0f0;
    font-weight: 600;
    min-width: 170px;
}
QPushButton#btn-confirm:hover    { background: #b91c1c; }
QPushButton#btn-confirm:disabled { background: #150000; border-color: #150000; color: #400000; }

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
    background: #4a0000;
    border: 1px solid #7f1d1d;
    border-radius: 6px;
    padding: 0 20px;
    color: #fef2f2;
    font-weight: 600;
    min-width: 90px;
}
QPushButton#btn-cancel:hover    { background: #7f1d1d; }
QPushButton#btn-cancel:disabled { background: #1a0000; border-color: #1a0000; color: #350000; }

/* ── Status label ────────────────────────────────────────────────── */
QLabel#status-label {
    color: #7f1d1d;
    font-size: 12px;
}

/* ── Inline confirmation banner ──────────────────────────────────── */
QFrame#confirm-bar {
    background: #130000;
    border: 1px solid #2a0000;
    border-left: 3px solid #dc2626;
    border-radius: 8px;
}

QLabel#confirm-bar-icon {
    font-size: 16px;
}

QLabel#confirm-bar-msg {
    color: #fca5a5;
    font-size: 12px;
}

QPushButton#btn-generate {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #dc2626, stop:1 #b91c1c);
    border: none;
    border-radius: 6px;
    padding: 0 20px;
    color: #fff0f0;
    font-weight: 700;
    font-size: 13px;
    min-width: 150px;
}
QPushButton#btn-generate:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #b91c1c, stop:1 #dc2626);
}
QPushButton#btn-generate:pressed {
    background: #991b1b;
}

/* ── Delete chapter button ───────────────────────────────────────── */
QPushButton#btn-delete-chapter {
    background: transparent;
    border: 1px solid #4a0000;
    border-radius: 5px;
    padding: 3px 10px;
    color: #9f2020;
    font-size: 11px;
}
QPushButton#btn-delete-chapter:hover {
    border-color: #ef4444;
    color: #ef4444;
    background: #1a0000;
}

/* ── Edit chapter button (preview header) ────────────────────────── */
QPushButton#btn-edit-chapter {
    background: transparent;
    border: 1px solid #2a0000;
    border-radius: 5px;
    padding: 3px 10px;
    color: #fca5a5;
    font-size: 11px;
}
QPushButton#btn-edit-chapter:hover {
    border-color: #dc2626;
    color: #f87171;
}

/* ── Chapter text editor ─────────────────────────────────────────── */
QTextEdit#chapter-text-edit {
    background: #080000;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 10px;
    color: #e2e8f0;
    font-size: 13px;
    selection-background-color: #dc2626;
}
QTextEdit#chapter-text-edit:focus {
    border-color: #dc2626;
}

/* ── Edit mode action buttons ────────────────────────────────────── */
QPushButton#btn-edit-save {
    background: #991b1b;
    border: 1px solid #b91c1c;
    border-radius: 6px;
    padding: 5px 16px;
    color: #fff0f0;
    font-weight: 600;
}
QPushButton#btn-edit-save:hover { background: #b91c1c; }

QPushButton#btn-edit-cancel {
    background: #0f0000;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 5px 14px;
    color: #fca5a5;
}
QPushButton#btn-edit-cancel:hover {
    border-color: #dc2626;
    color: #e2e8f0;
}

/* ── Regenerate button on chapter card ───────────────────────────── */
QPushButton#btn-regen {
    background: #0f0000;
    border: 1px solid #2a0000;
    border-radius: 4px;
    color: #9f2020;
    font-size: 13px;
    font-weight: 700;
}
QPushButton#btn-regen:hover {
    background: #14532d;
    border-color: #16a34a;
    color: #22c55e;
}
QPushButton#btn-regen:disabled {
    color: #250000;
    border-color: #1e0000;
}

/* ── Settings dialog ─────────────────────────────────────────────── */
QDialog {
    background: #080000;
}

QLineEdit#settings-input {
    background: #0f0000;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
    selection-background-color: #dc2626;
}
QLineEdit#settings-input:focus {
    border-color: #dc2626;
}
QLineEdit#settings-input:disabled {
    color: #4a0000;
    border-color: #1e0000;
    background: #080000;
}

QComboBox {
    background: #0f0000;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
}
QComboBox:disabled {
    color: #4a0000;
    background: #080000;
}
QComboBox QAbstractItemView {
    background: #0f0000;
    border: 1px solid #2a0000;
    color: #e2e8f0;
    selection-background-color: #dc2626;
}
QComboBox::drop-down { border: none; }

QComboBox#genre-combo {
    background: #1a0000;
    border: 1px solid #dc2626;
    border-radius: 5px;
    padding: 4px 8px;
    color: #f87171;
    font-size: 12px;
    font-weight: 600;
}
QComboBox#genre-combo:hover {
    background: #250000;
}
QComboBox#genre-combo QAbstractItemView {
    background: #0f0000;
    border: 1px solid #dc2626;
    color: #fca5a5;
    selection-background-color: #dc2626;
    selection-color: #ffffff;
}

QCheckBox {
    color: #fca5a5;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #2a0000;
    border-radius: 4px;
    background: #0f0000;
}
QCheckBox::indicator:checked {
    background: #dc2626;
    border-color: #dc2626;
}

QLabel#settings-hint {
    color: #7f1d1d;
    font-size: 11px;
}

QLabel#settings-section {
    color: #dc2626;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding-top: 18px;
    padding-bottom: 4px;
    border-bottom: 1px solid #2a0000;
}

QDialogButtonBox QPushButton {
    background: #0f0000;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 6px 18px;
    color: #fca5a5;
    min-width: 70px;
}
QDialogButtonBox QPushButton:hover {
    border-color: #dc2626;
    color: #e2e8f0;
}
QDialogButtonBox QPushButton[text="OK"] {
    background: #991b1b;
    border-color: #b91c1c;
    color: #fff0f0;
    font-weight: 600;
}
QDialogButtonBox QPushButton[text="OK"]:hover {
    background: #b91c1c;
}

/* ── Scrollbars ──────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a0000;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover  { background: #dc2626; }
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
    background: #2a0000;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #dc2626; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal     { width: 0; }
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal     { background: transparent; }

/* ── Scrollable body ─────────────────────────────────────────────── */
QWidget#scroll-body {
    background: #000000;
}

/* ── Info bar (top card row) ─────────────────────────────────────── */
QFrame#info-bar {
    background: transparent;
}

QFrame#info-card {
    background: #0a0000;
    border: 1px solid #1e0000;
    border-radius: 10px;
}

QLabel#info-card-title {
    color: #7f1d1d;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

QLabel#info-card-meta {
    color: #9f2020;
    font-size: 11px;
}

/* ── Section containers (pipeline + chapter) ─────────────────────── */
QFrame#pipeline-section,
QFrame#chapter-section {
    background: #0a0000;
    border: 1px solid #1e0000;
    border-radius: 10px;
}

QFrame#section-header {
    background: transparent;
    border-radius: 10px;
}

QLabel#section-title {
    color: #7f1d1d;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.9px;
}

QPushButton#section-toggle-btn {
    background: transparent;
    border: 1px solid #2a0000;
    border-radius: 4px;
    color: #7f1d1d;
    font-size: 11px;
    font-weight: 700;
    padding: 0;
}
QPushButton#section-toggle-btn:hover {
    border-color: #dc2626;
    color: #f87171;
}

/* ── Settings adaptation toggle ──────────────────────────────────── */
QPushButton#toggle-btn {
    background: #0f0000;
    border: 1px solid #2a0000;
    border-radius: 12px;
    color: #9f2020;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    min-width: 52px;
    max-width: 52px;
    padding: 4px 0;
}
QPushButton#toggle-btn:checked {
    background: #b91c1c;
    border-color: #dc2626;
    color: #ffffff;
}
QPushButton#toggle-btn:hover {
    border-color: #dc2626;
}
QPushButton#toggle-btn:checked:hover {
    background: #dc2626;
}

QWidget#section-content {
    background: transparent;
}

/* ── Stage rows ──────────────────────────────────────────────────── */
QFrame#stage-row {
    background: transparent;
}

QFrame#stage-sep {
    background: #0f0000;
}

QLabel#stage-name {
    color: #fca5a5;
    font-size: 13px;
    font-weight: 600;
}

QLabel#stage-desc {
    color: #4a0000;
    font-size: 12px;
}

QLabel#stage-detail {
    color: #9f2020;
    font-size: 11px;
}

/* Stage status icons */
QFrame#stage-icon-pending { background: #250000; border-radius: 5px; }
QFrame#stage-icon-running { background: #f87171; border-radius: 5px; }
QFrame#stage-icon-done    { background: #22c55e; border-radius: 5px; }
QFrame#stage-icon-error   { background: #ef4444; border-radius: 5px; }

/* Stage state labels */
QLabel#stage-state-pending { color: #250000; font-size: 11px; }
QLabel#stage-state-running { color: #f87171; font-size: 11px; }
QLabel#stage-state-done    { color: #22c55e; font-size: 11px; }
QLabel#stage-state-error   { color: #ef4444; font-size: 11px; }

/* ── Expandable chapter cards ────────────────────────────────────── */
QFrame#exp-chapter-card {
    background: #0a0000;
}

QFrame#exp-card-header {
    background: transparent;
}

QFrame#exp-card-header:hover {
    background: #120000;
}

QFrame#exp-card-header-active {
    background: #1a0000;
}

QWidget#exp-card-content {
    background: #000000;
}

QLabel#exp-icon {
    color: #4a0000;
    font-size: 11px;
}

QFrame#card-sep {
    background: #0f0000;
}

/* ── Voice Designer dialog ───────────────────────────────────────── */
QFrame#vd-genre-panel {
    background: #000000;
    border-right: 1px solid #1e0000;
}

QListWidget#vd-genre-list {
    background: #000000;
    border: none;
    color: #fca5a5;
    font-size: 13px;
    outline: none;
}
QListWidget#vd-genre-list::item {
    padding: 8px 12px;
    border-radius: 4px;
}
QListWidget#vd-genre-list::item:selected {
    background: #3b0000;
    color: #fca5a5;
}
QListWidget#vd-genre-list::item:hover:!selected {
    background: #120000;
}

QLabel#vd-spec-label {
    color: #7f1d1d;
    font-size: 11px;
}

QLineEdit#vd-spec-field {
    background: #080000;
    border: 1px solid #2a0000;
    border-radius: 4px;
    padding: 4px 8px;
    color: #fca5a5;
    font-size: 12px;
}
QLineEdit#vd-spec-field:focus {
    border-color: #dc2626;
}

QLabel#vd-genre-title {
    color: #f87171;
    font-size: 18px;
    font-weight: 700;
    padding-bottom: 6px;
}

QTextEdit#vd-instruct-view {
    background: #080000;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 10px;
    color: #fca5a5;
    font-size: 12px;
}
QTextEdit#vd-instruct-view:focus {
    border-color: #dc2626;
}

QPushButton#vd-reset-prompt-btn {
    background: transparent;
    border: none;
    color: #7f1d1d;
    font-size: 11px;
    padding: 2px 4px;
}
QPushButton#vd-reset-prompt-btn:hover {
    color: #f87171;
}

QProgressBar#vd-progress {
    background: #1c0000;
    border: none;
    border-radius: 4px;
    max-height: 6px;
}
QProgressBar#vd-progress::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #dc2626, stop:1 #f87171);
    border-radius: 4px;
}

QLabel#vd-log-msg {
    color: #7f1d1d;
    font-size: 11px;
}

QLabel#vd-status-text {
    color: #9f2020;
    font-size: 12px;
}

QPushButton#vd-use-btn {
    background: #15803d;
    border: 1px solid #16a34a;
    border-radius: 6px;
    padding: 6px 18px;
    color: #f0fdf4;
    font-weight: 600;
}
QPushButton#vd-use-btn:hover    { background: #16a34a; }
QPushButton#vd-use-btn:disabled {
    background: #1a2e1a;
    border-color: #1a2e1a;
    color: #3a5a3a;
}

QPushButton#vd-replay-btn {
    background: transparent;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 6px 14px;
    color: #fca5a5;
    font-size: 12px;
}
QPushButton#vd-replay-btn:hover { border-color: #dc2626; color: #f87171; }
QPushButton#vd-replay-btn:disabled { color: #250000; border-color: #1e0000; }

QPushButton#vd-reset-btn {
    background: transparent;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 6px 14px;
    color: #9f2020;
    font-size: 12px;
}
QPushButton#vd-reset-btn:hover {
    border-color: #ef4444;
    color: #ef4444;
}
QPushButton#vd-reset-btn:disabled { color: #250000; border-color: #1e0000; }

QPushButton#vd-close-btn {
    background: transparent;
    border: 1px solid #2a0000;
    border-radius: 6px;
    padding: 6px 20px;
    color: #fca5a5;
}
QPushButton#vd-close-btn:hover {
    border-color: #9f2020;
    color: #e2e8f0;
}
"""
