"""Dark Amber / Warm Black stylesheet for pdf2voice."""

DARK_STYLESHEET = """
/* ── Global ──────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0f0d0b;
    color: #e2d9cc;
    font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
    font-size: 13px;
}

QLabel {
    background: transparent;
}

QSplitter::handle {
    background: #1e1810;
}
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }

/* ── Header bar ──────────────────────────────────────────────────── */
QFrame#header-bar {
    background-color: #0b0907;
    border-bottom: 1px solid #1e1810;
}

QLabel#app-title {
    font-size: 18px;
    font-weight: 700;
    color: #fbbf24;
    letter-spacing: 0.5px;
}

QPushButton#header-btn {
    background: transparent;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 6px 14px;
    color: #fbbf24;
    font-size: 12px;
}
QPushButton#header-btn:hover {
    border-color: #d97706;
    color: #fcd34d;
    background: #1e1810;
}

/* ── Structural panels ───────────────────────────────────────────── */
QFrame#left-panel {
    background: #0f0d0b;
    border-right: 1px solid #1e1810;
}
QFrame#center-panel {
    background: #0f0d0b;
}
QFrame#footer-bar {
    background: #0b0907;
    border-top: 1px solid #1e1810;
}

/* ── Group boxes ─────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #1e1810;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: 600;
    color: #92400e;
    font-size: 11px;
    letter-spacing: 0.8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #92400e;
}

/* ── Path input ──────────────────────────────────────────────────── */
QLineEdit#path-edit {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 7px 10px;
    color: #e2d9cc;
    selection-background-color: #d97706;
}
QLineEdit#path-edit:focus {
    border-color: #d97706;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton#browse-btn {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 7px 12px;
    color: #fbbf24;
}
QPushButton#browse-btn:hover {
    background: #1e1810;
    border-color: #d97706;
    color: #e2d9cc;
}

/* ── Voice gender pill toggle ────────────────────────────────────── */
QPushButton#voice-pill-left,
QPushButton#voice-pill-right {
    background: #13110e;
    border: 1px solid #3d2e1e;
    color: #92400e;
    font-size: 13px;
    font-weight: 500;
    padding: 0 16px;
}
QPushButton#voice-pill-left  { border-radius: 0; border-top-left-radius: 8px; border-bottom-left-radius: 8px; border-right: none; }
QPushButton#voice-pill-right { border-radius: 0; border-top-right-radius: 8px; border-bottom-right-radius: 8px; }

QPushButton#voice-pill-left:hover,
QPushButton#voice-pill-right:hover {
    background: #1e1810;
    color: #fbbf24;
}

QPushButton#voice-pill-left-active {
    background: #3d2c0a;
    border: 1px solid #d97706;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: none;
    color: #fbbf24;
    font-size: 13px;
    font-weight: 600;
    padding: 0 16px;
}
QPushButton#voice-pill-right-active {
    background: #3d2c0a;
    border: 1px solid #d97706;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    color: #fbbf24;
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
    color: #78450e;
    font-size: 11px;
}
QLabel#settings-val {
    color: #fbbf24;
    font-size: 11px;
}

/* ── Metadata card values ────────────────────────────────────────── */
QLabel#metadata-val {
    color: #fbbf24;
    font-size: 12px;
}

/* ── Reanalyze button ────────────────────────────────────────────── */
QPushButton#btn-reanalyze {
    background: transparent;
    border: 1px solid #3d2e1e;
    border-radius: 5px;
    padding: 2px 10px;
    color: #92400e;
    font-size: 11px;
}
QPushButton#btn-reanalyze:hover {
    border-color: #d97706;
    color: #fbbf24;
    background: #1a1410;
}
QPushButton#btn-reanalyze:disabled {
    color: #3a2610;
    border-color: #1e1810;
}

/* ── Panel section titles ────────────────────────────────────────── */
QLabel#panel-title {
    font-weight: 700;
    font-size: 11px;
    color: #92400e;
    letter-spacing: 1px;
    padding-bottom: 4px;
}

/* ── Pipeline card ───────────────────────────────────────────────── */
QWidget#pipeline-panel {
    background: #13110e;
    border: 1px solid #1e1810;
    border-radius: 10px;
}

/* Step dots */
QLabel#step-dot-pending {
    background: #1e1810;
    border: 2px solid #3d2e1e;
    border-radius: 14px;
    color: #78450e;
    font-size: 11px;
    font-weight: 700;
}
QLabel#step-dot-running {
    background: #3d2c0a;
    border: 2px solid #d97706;
    border-radius: 14px;
    color: #fbbf24;
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
    background: #3b1308;
    border: 2px solid #ef4444;
    border-radius: 14px;
    color: #ef4444;
    font-size: 11px;
    font-weight: 700;
}

QLabel#step-sep {
    background: #1e1810;
    margin-top: 12px;
}

QLabel#step-label {
    color: #78450e;
    font-size: 10px;
    max-width: 80px;
}

/* Pipeline progress bar */
QProgressBar#pipeline-bar {
    background: #1e1810;
    border: none;
    border-radius: 4px;
}
QProgressBar#pipeline-bar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #d97706, stop:1 #fbbf24);
    border-radius: 4px;
}

QLabel#pipeline-spinner {
    color: #fbbf24;
    font-size: 15px;
}

QLabel#pipeline-stage-lbl {
    color: #92400e;
    font-size: 11px;
}

/* ── Chapter list ────────────────────────────────────────────────── */
QWidget#chapter-panel {
    background: #13110e;
    border: 1px solid #1e1810;
    border-radius: 10px;
}

QFrame#side-panel-header {
    background: transparent;
}

QLabel#side-panel-title {
    color: #92400e;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

QFrame#panel-sep {
    background: #1e1810;
}

QWidget#panel-scroll-content {
    background: #13110e;
}

QFrame#chapter-card {
    background: #0f0d0b;
    border-radius: 0px;
    border-left: none;
}

QFrame#card-dot-pending { background: #2a1e08; border-radius: 4px; }
QFrame#card-dot-running { background: #fbbf24; border-radius: 4px; }
QFrame#card-dot-done    { background: #22c55e; border-radius: 4px; }
QFrame#card-dot-error   { background: #ef4444; border-radius: 4px; }

QLabel#card-num {
    color: #523210;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel#card-title {
    color: #a16207;
    font-size: 12px;
}

/* ── Preview panel ───────────────────────────────────────────────── */
QWidget#preview-panel {
    background: #13110e;
    border: 1px solid #1e1810;
    border-radius: 10px;
}

QWidget#preview-content {
    background: #13110e;
}

QLabel#preview-placeholder {
    color: #2a1e08;
    font-size: 13px;
    padding: 20px;
}

QLabel#preview-chapter-title {
    color: #fbbf24;
    font-size: 16px;
    font-weight: 700;
}

QLabel#preview-meta {
    color: #523210;
    font-size: 11px;
}

QFrame#preview-announcement {
    background: transparent;
    border: none;
    border-left: 2px solid #d97706;
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
    color: #523210;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

QFrame#preview-chunk-card {
    background: transparent;
    border: none;
    border-left: 2px solid #2a1e08;
    border-radius: 0;
}

QLabel#chunk-badge {
    background: #3d2c0a;
    color: #fbbf24;
    font-size: 11px;
    font-weight: 700;
    border-radius: 11px;
}

QLabel#chunk-chars {
    color: #3a2610;
    font-size: 10px;
    font-family: monospace;
}

QLabel#chunk-body {
    color: #a16207;
    font-size: 12px;
    padding-left: 4px;
}

/* ── Log card ────────────────────────────────────────────────────── */
QWidget#log-panel {
    background: #13110e;
    border: 1px solid #1e1810;
    border-radius: 10px;
}

QTextEdit#log-text {
    background: transparent;
    border: none;
    color: #e2d9cc;
    font-size: 12px;
    selection-background-color: #d97706;
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
    background: #b45309;
    border: 1px solid #d97706;
    border-radius: 6px;
    padding: 0 20px;
    color: #fefce8;
    font-weight: 600;
    min-width: 170px;
}
QPushButton#btn-confirm:hover    { background: #d97706; }
QPushButton#btn-confirm:disabled { background: #1a1408; border-color: #1a1408; color: #40300a; }

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
    background: #2a1e08;
    border: 1px solid #78450e;
    border-radius: 6px;
    padding: 0 20px;
    color: #fef3c7;
    font-weight: 600;
    min-width: 90px;
}
QPushButton#btn-cancel:hover    { background: #3d2c0a; }
QPushButton#btn-cancel:disabled { background: #1a1408; border-color: #1a1408; color: #3a2610; }

/* ── Status label ────────────────────────────────────────────────── */
QLabel#status-label {
    color: #78450e;
    font-size: 12px;
}

/* ── Inline confirmation banner ──────────────────────────────────── */
QFrame#confirm-bar {
    background: #13100a;
    border: 1px solid #3d2e1e;
    border-left: 3px solid #d97706;
    border-radius: 8px;
}

QLabel#confirm-bar-icon {
    font-size: 16px;
}

QLabel#confirm-bar-msg {
    color: #fbbf24;
    font-size: 12px;
}

QPushButton#btn-generate {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #d97706, stop:1 #b45309);
    border: none;
    border-radius: 6px;
    padding: 0 20px;
    color: #fefce8;
    font-weight: 700;
    font-size: 13px;
    min-width: 150px;
}
QPushButton#btn-generate:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f59e0b, stop:1 #d97706);
}
QPushButton#btn-generate:pressed {
    background: #92400e;
}

/* ── Delete chapter button ───────────────────────────────────────── */
QPushButton#btn-delete-chapter {
    background: transparent;
    border: 1px solid #3a2610;
    border-radius: 5px;
    padding: 3px 10px;
    color: #a16207;
    font-size: 11px;
}
QPushButton#btn-delete-chapter:hover {
    border-color: #ef4444;
    color: #ef4444;
    background: #1e1008;
}

/* ── Edit chapter button ─────────────────────────────────────────── */
QPushButton#btn-edit-chapter {
    background: transparent;
    border: 1px solid #3d2e1e;
    border-radius: 5px;
    padding: 3px 10px;
    color: #fbbf24;
    font-size: 11px;
}
QPushButton#btn-edit-chapter:hover {
    border-color: #d97706;
    color: #fcd34d;
}

/* ── Chapter text editor ─────────────────────────────────────────── */
QTextEdit#chapter-text-edit {
    background: #0f0d0b;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 10px;
    color: #e2d9cc;
    font-size: 13px;
    selection-background-color: #d97706;
}
QTextEdit#chapter-text-edit:focus {
    border-color: #d97706;
}

/* ── Edit mode action buttons ────────────────────────────────────── */
QPushButton#btn-edit-save {
    background: #b45309;
    border: 1px solid #d97706;
    border-radius: 6px;
    padding: 5px 16px;
    color: #fefce8;
    font-weight: 600;
}
QPushButton#btn-edit-save:hover { background: #d97706; }

QPushButton#btn-edit-cancel {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 5px 14px;
    color: #fbbf24;
}
QPushButton#btn-edit-cancel:hover {
    border-color: #d97706;
    color: #e2d9cc;
}

/* ── Regenerate button on chapter card ───────────────────────────── */
QPushButton#btn-regen {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 4px;
    color: #a16207;
    font-size: 13px;
    font-weight: 700;
}
QPushButton#btn-regen:hover {
    background: #14532d;
    border-color: #16a34a;
    color: #22c55e;
}
QPushButton#btn-regen:disabled {
    color: #2a1e08;
    border-color: #1e1810;
}

/* ── Settings dialog ─────────────────────────────────────────────── */
QDialog {
    background: #0f0d0b;
}

QLineEdit#settings-input {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2d9cc;
    selection-background-color: #d97706;
}
QLineEdit#settings-input:focus {
    border-color: #d97706;
}
QLineEdit#settings-input:disabled {
    color: #3a2610;
    border-color: #1e1810;
    background: #0f0d0b;
}

QComboBox {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2d9cc;
}
QComboBox:disabled {
    color: #3a2610;
    background: #0f0d0b;
}
QComboBox QAbstractItemView {
    background: #13110e;
    border: 1px solid #3d2e1e;
    color: #e2d9cc;
    selection-background-color: #d97706;
}
QComboBox::drop-down { border: none; }

QComboBox#genre-combo {
    background: #1e1810;
    border: 1px solid #d97706;
    border-radius: 5px;
    padding: 4px 8px;
    color: #fbbf24;
    font-size: 12px;
    font-weight: 600;
}
QComboBox#genre-combo:hover {
    background: #2a1e08;
}
QComboBox#genre-combo QAbstractItemView {
    background: #13110e;
    border: 1px solid #d97706;
    color: #fbbf24;
    selection-background-color: #d97706;
    selection-color: #0f0d0b;
}

QCheckBox {
    color: #fbbf24;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #3d2e1e;
    border-radius: 4px;
    background: #13110e;
}
QCheckBox::indicator:checked {
    background: #d97706;
    border-color: #d97706;
}

QLabel#settings-hint {
    color: #78450e;
    font-size: 11px;
}

QLabel#settings-section {
    color: #d97706;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding-top: 18px;
    padding-bottom: 4px;
    border-bottom: 1px solid #3d2e1e;
}

QDialogButtonBox QPushButton {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 6px 18px;
    color: #fbbf24;
    min-width: 70px;
}
QDialogButtonBox QPushButton:hover {
    border-color: #d97706;
    color: #e2d9cc;
}
QDialogButtonBox QPushButton[text="OK"] {
    background: #b45309;
    border-color: #d97706;
    color: #fefce8;
    font-weight: 600;
}
QDialogButtonBox QPushButton[text="OK"]:hover {
    background: #d97706;
}

/* ── Scrollbars ──────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3d2e1e;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover  { background: #d97706; }
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
    background: #3d2e1e;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #d97706; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal     { width: 0; }
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal     { background: transparent; }

/* ── Scrollable body ─────────────────────────────────────────────── */
QWidget#scroll-body {
    background: #0f0d0b;
}

/* ── Info bar ────────────────────────────────────────────────────── */
QFrame#info-bar {
    background: transparent;
}

QFrame#info-card {
    background: #13110e;
    border: 1px solid #1e1810;
    border-radius: 10px;
}

QLabel#info-card-title {
    color: #78450e;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

QLabel#info-card-meta {
    color: #92400e;
    font-size: 11px;
}

/* ── Section containers ──────────────────────────────────────────── */
QFrame#pipeline-section,
QFrame#chapter-section {
    background: #13110e;
    border: 1px solid #1e1810;
    border-radius: 10px;
}

QFrame#section-header {
    background: transparent;
    border-radius: 10px;
}

QLabel#section-title {
    color: #78450e;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.9px;
}

QPushButton#section-toggle-btn {
    background: transparent;
    border: 1px solid #3d2e1e;
    border-radius: 4px;
    color: #78450e;
    font-size: 11px;
    font-weight: 700;
    padding: 0;
}
QPushButton#section-toggle-btn:hover {
    border-color: #d97706;
    color: #fbbf24;
}

/* ── Settings adaptation toggle ──────────────────────────────────── */
QPushButton#toggle-btn {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 12px;
    color: #92400e;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    min-width: 52px;
    max-width: 52px;
    padding: 4px 0;
}
QPushButton#toggle-btn:checked {
    background: #b45309;
    border-color: #d97706;
    color: #fefce8;
}
QPushButton#toggle-btn:hover {
    border-color: #d97706;
}
QPushButton#toggle-btn:checked:hover {
    background: #d97706;
}

QWidget#section-content {
    background: transparent;
}

/* ── Stage rows ──────────────────────────────────────────────────── */
QFrame#stage-row {
    background: transparent;
}

QFrame#stage-sep {
    background: #13110e;
}

QLabel#stage-name {
    color: #fbbf24;
    font-size: 13px;
    font-weight: 600;
}

QLabel#stage-desc {
    color: #3a2610;
    font-size: 12px;
}

QLabel#stage-detail {
    color: #92400e;
    font-size: 11px;
}

QFrame#stage-icon-pending { background: #2a1e08; border-radius: 5px; }
QFrame#stage-icon-running { background: #fbbf24; border-radius: 5px; }
QFrame#stage-icon-done    { background: #22c55e; border-radius: 5px; }
QFrame#stage-icon-error   { background: #ef4444; border-radius: 5px; }

QLabel#stage-state-pending { color: #2a1e08; font-size: 11px; }
QLabel#stage-state-running { color: #fbbf24; font-size: 11px; }
QLabel#stage-state-done    { color: #22c55e; font-size: 11px; }
QLabel#stage-state-error   { color: #ef4444; font-size: 11px; }

/* ── Expandable chapter cards ────────────────────────────────────── */
QFrame#exp-chapter-card {
    background: #13110e;
}

QFrame#exp-card-header {
    background: transparent;
}

QFrame#exp-card-header:hover {
    background: #1a1610;
}

QFrame#exp-card-header-active {
    background: #211a0f;
}

QWidget#exp-card-content {
    background: #0f0d0b;
}

QLabel#exp-icon {
    color: #523210;
    font-size: 11px;
}

QFrame#card-sep {
    background: #1a1610;
}

/* ── Voice Designer dialog ───────────────────────────────────────── */
QFrame#vd-genre-panel {
    background: #0f0d0b;
    border-right: 1px solid #1e1810;
}

QListWidget#vd-genre-list {
    background: #0f0d0b;
    border: none;
    color: #fbbf24;
    font-size: 13px;
    outline: none;
}
QListWidget#vd-genre-list::item {
    padding: 8px 12px;
    border-radius: 4px;
}
QListWidget#vd-genre-list::item:selected {
    background: #3d2c0a;
    color: #fbbf24;
}
QListWidget#vd-genre-list::item:hover:!selected {
    background: #1a1610;
}

QLabel#vd-spec-label {
    color: #78450e;
    font-size: 11px;
}

QLineEdit#vd-spec-field {
    background: #0f0d0b;
    border: 1px solid #3d2e1e;
    border-radius: 4px;
    padding: 4px 8px;
    color: #fbbf24;
    font-size: 12px;
}
QLineEdit#vd-spec-field:focus {
    border-color: #d97706;
}

QLabel#vd-genre-title {
    color: #fbbf24;
    font-size: 18px;
    font-weight: 700;
    padding-bottom: 6px;
}

QTextEdit#vd-instruct-view {
    background: #0f0d0b;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 10px;
    color: #fbbf24;
    font-size: 12px;
}
QTextEdit#vd-instruct-view:focus {
    border-color: #d97706;
}

QPushButton#vd-reset-prompt-btn {
    background: transparent;
    border: none;
    color: #78450e;
    font-size: 11px;
    padding: 2px 4px;
}
QPushButton#vd-reset-prompt-btn:hover {
    color: #fbbf24;
}

QProgressBar#vd-progress {
    background: #1e1810;
    border: none;
    border-radius: 4px;
    max-height: 6px;
}
QProgressBar#vd-progress::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #d97706, stop:1 #fbbf24);
    border-radius: 4px;
}

QLabel#vd-log-msg {
    color: #78450e;
    font-size: 11px;
}

QLabel#vd-status-text {
    color: #92400e;
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
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 6px 14px;
    color: #fbbf24;
    font-size: 12px;
}
QPushButton#vd-replay-btn:hover { border-color: #d97706; color: #fcd34d; }
QPushButton#vd-replay-btn:disabled { color: #2a1e08; border-color: #1e1810; }

QPushButton#vd-reset-btn {
    background: transparent;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 6px 14px;
    color: #92400e;
    font-size: 12px;
}
QPushButton#vd-reset-btn:hover {
    border-color: #ef4444;
    color: #ef4444;
}
QPushButton#vd-reset-btn:disabled { color: #2a1e08; border-color: #1e1810; }

QPushButton#vd-close-btn {
    background: transparent;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 6px 20px;
    color: #fbbf24;
}
QPushButton#vd-close-btn:hover {
    border-color: #92400e;
    color: #e2d9cc;
}

QPushButton#vd-ai-fill-btn {
    background: #3d2c0a;
    border: 1px solid #d97706;
    border-radius: 6px;
    padding: 6px 14px;
    color: #fbbf24;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#vd-ai-fill-btn:hover {
    background: #524010;
    border-color: #fbbf24;
}
QPushButton#vd-ai-fill-btn:disabled {
    color: #2a1e08;
    border-color: #1e1810;
    background: #13110e;
}

QLineEdit#vd-ai-prompt {
    background: #13110e;
    border: 1px solid #3d2e1e;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2d9cc;
    font-size: 12px;
}
QLineEdit#vd-ai-prompt:focus {
    border-color: #d97706;
}

QComboBox#vd-spec-combo {
    background: #0f0d0b;
    border: 1px solid #3d2e1e;
    border-radius: 4px;
    padding: 4px 8px;
    color: #fbbf24;
    font-size: 12px;
}
QComboBox#vd-spec-combo:focus {
    border-color: #d97706;
}
QComboBox#vd-spec-combo QAbstractItemView {
    background: #13110e;
    border: 1px solid #3d2e1e;
    color: #fbbf24;
    selection-background-color: #d97706;
    selection-color: #0f0d0b;
}
"""
