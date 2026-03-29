"""
Central theme system for AttenSync.
Usage:
    import theme
    theme.set_app_mode("dark", app)   # pass QApplication instance
    t = theme.current_palette()       # get current colour dict
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

# ── Palettes ────────────────────────────────────────────────────────────────
LIGHT = {
    "bg_main":          "#f0f2f8",
    "bg_card":          "#ffffff",
    "bg_panel":         "#f7f8ff",
    "bg_topbar":        "#ffffff",
    "bg_sidebar":       "#1e2a3a",
    "sidebar_text":     "#c8d6e3",
    "sidebar_hover":    "#2d3e50",
    "sidebar_active":   "#2196F3",
    "text_primary":     "#1a1a2e",
    "text_secondary":   "#55557a",
    "text_muted":       "#9999bb",
    "border":           "#e0e4f0",
    "accent":           "#3F51B5",
    "accent_hover":     "#303f9f",
    "input_bg":         "#ffffff",
    "input_border":     "#d0d7de",
    "table_alt":        "#f5f6ff",
    "header_bg":        "#eceeff",
    "success":          "#388E3C",
    "error":            "#D32F2F",
    "warning":          "#F57C00",
    "mode":             "light",
}

DARK = {
    "bg_main":          "#0d1117",
    "bg_card":          "#161b22",
    "bg_panel":         "#1a1d2e",
    "bg_topbar":        "#13151f",
    "bg_sidebar":       "#0d1117",
    "sidebar_text":     "#8b949e",
    "sidebar_hover":    "#21262d",
    "sidebar_active":   "#1f6feb",
    "text_primary":     "#e6edf3",
    "text_secondary":   "#8b949e",
    "text_muted":       "#484f58",
    "border":           "#21262d",
    "accent":           "#1f6feb",
    "accent_hover":     "#388bfd",
    "input_bg":         "#0d1117",
    "input_border":     "#30363d",
    "table_alt":        "#0d1117",
    "header_bg":        "#161b22",
    "success":          "#3fb950",
    "error":            "#f85149",
    "warning":          "#d29922",
    "mode":             "dark",
}

_MODE = "light"

def current_mode() -> str:
    return _MODE

def current_palette() -> dict:
    return LIGHT if _MODE == "light" else DARK

def toggle(app: QApplication = None) -> str:
    global _MODE
    _MODE = "dark" if _MODE == "light" else "light"
    if app:
        app.setStyleSheet(build_stylesheet())
    return _MODE

def set_app_mode(mode: str, app: QApplication = None):
    global _MODE
    _MODE = mode
    if app:
        app.setStyleSheet(build_stylesheet())

def build_stylesheet() -> str:
    t = current_palette()
    return f"""
    /* ── Root windows ─────────────────────────────────── */
    QMainWindow {{
        background-color: {t["bg_main"]};
    }}
    QDialog {{
        background-color: {t["bg_card"]};
    }}
    QMessageBox {{
        background-color: {t["bg_card"]};
    }}
    QMessageBox QLabel {{
        color: {t["text_primary"]};
        background: transparent;
        font-size: 13px;
    }}
    QMessageBox QPushButton, QDialogButtonBox QPushButton {{
        background-color: {t["accent"]};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 6px 20px;
        font-size: 12px;
        font-weight: 600;
        min-width: 72px;
        min-height: 30px;
    }}
    QMessageBox QPushButton:hover, QDialogButtonBox QPushButton:hover {{ background-color: {t["accent_hover"]}; }}
    /* ── Frame / generic panels inside dialogs ─────────── */
    QFrame {{
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
    }}
    /* A transparent helper for inner layout containers */
    QWidget#innerWidget {{
        background-color: transparent;
    }}
    /* ── Splitter ───────────────────────────────────────── */
    QSplitter::handle {{
        background-color: {t["border"]};
    }}
    /* ── Labels ─────────────────────────────────────────── */
    QLabel {{
        color: {t["text_primary"]};
        background: transparent;
        font-size: 13px;
        font-weight: 500;
    }}
    QGroupBox {{
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 6px;
        margin-top: 14px;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        color: {t["accent"]};
        font-weight: 700;
    }}
    /* ── Buttons (global fallback) ─────────────────────── */
    QPushButton {{
        background-color: {t["accent"]};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 600;
        min-height: 30px;
    }}
    QPushButton:hover {{ background-color: {t["accent_hover"]}; }}
    QPushButton:pressed {{ background-color: {t["accent_hover"]}; }}
    QPushButton:disabled {{
        background-color: {t["border"]};
        color: {t["text_muted"]};
    }}
    /* ── Inputs ─────────────────────────────────────────── */
    QLineEdit, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QComboBox {{
        background-color: {t["input_bg"]};
        color: {t["text_primary"]};
        border: 1px solid {t["input_border"]};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 13px;
        min-height: 30px;
    }}
    QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 2px solid {t["accent"]};
        background-color: {t["bg_card"]};
    }}
    QLineEdit:disabled, QDateEdit:disabled, QTimeEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
        background-color: {t["border"]};
        color: {t["text_muted"]};
    }}

    /* ── Custom SVG Arrows ─────────────────────────────── */
    QComboBox::drop-down, QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {{
        border: none;
        width: 32px;
    }}
    QComboBox::down-arrow {{
        image: url(ui/icons/down.svg);
        width: 12px;
        height: 12px;
    }}
    QDateEdit::down-arrow {{
        image: url(ui/icons/calendar.svg);
        width: 14px;
        height: 14px;
    }}
    QTimeEdit::down-arrow {{
        image: url(ui/icons/down.svg);
        width: 12px;
        height: 12px;
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button {{
        image: url(ui/icons/up.svg);
        border: none;
        width: 20px;
        margin-top: 4px;
    }}
    QSpinBox::down-button, QDoubleSpinBox::down-button, QTimeEdit::down-button {{
        image: url(ui/icons/down.svg);
        border: none;
        width: 20px;
        margin-bottom: 4px;
    }}

    /* ── Dropdowns ─────────────────────────────────────── */
    QComboBox QAbstractItemView, QDateEdit QAbstractItemView, QTimeEdit QAbstractItemView, QDateTimeEdit QAbstractItemView {{
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
        selection-background-color: {t["accent"]};
        selection-color: white;
        border: 1px solid {t["border"]};
        outline: none;
        padding: 4px;
    }}
    /* ── Tables ────────────────────────────────────────── */
    QTableWidget, QTableView {{
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
        gridline-color: {t["border"]};
        border: 1px solid {t["border"]};
        border-radius: 6px;
        outline: none;
        alternate-background-color: {t["table_alt"]};
    }}
    QTableWidget::item, QTableView::item {{
        color: {t["text_primary"]};
        padding: 5px 8px;
    }}
    QTableWidget::item:selected, QTableView::item:selected {{
        background-color: {t["accent"]};
        color: white;
    }}
    QTableWidget::item:hover, QTableView::item:hover {{
        background-color: {t["header_bg"]};
        color: {t["text_primary"]};
    }}
    QHeaderView::section {{
        background-color: {t["header_bg"]};
        color: {t["text_primary"]};
        padding: 7px 8px;
        border: none;
        border-bottom: 2px solid {t["accent"]};
        font-weight: 700;
        font-size: 12px;
    }}
    QHeaderView::section:checked {{
        background-color: {t["accent"]};
        color: white;
    }}
    QHeaderView {{
        background-color: {t["header_bg"]};
    }}
    /* ── List / Tree ───────────────────────────────────── */
    QListWidget, QTreeWidget, QListView, QTreeView {{
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 5px;
        outline: none;
    }}
    QListWidget::item, QTreeWidget::item {{
        color: {t["text_primary"]};
        padding: 4px 6px;
    }}
    QListWidget::item:selected, QTreeWidget::item:selected {{
        background-color: {t["accent"]};
        color: white;
    }}
    QListWidget::item:hover, QTreeWidget::item:hover {{
        background-color: {t["header_bg"]};
        color: {t["text_primary"]};
    }}
    /* ── Tabs ──────────────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {t["border"]};
        background: {t["bg_card"]};
        border-radius: 0 6px 6px 6px;
    }}
    QTabBar::tab {{
        background: {t["header_bg"]};
        color: {t["text_primary"]};
        padding: 8px 22px;
        border: 1px solid {t["border"]};
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        margin-right: 2px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: {t["accent"]};
        color: white;
        border-color: {t["accent"]};
    }}
    QTabBar::tab:hover:!selected {{
        background: {t["bg_panel"]};
        color: {t["text_primary"]};
    }}
    /* ── Scroll bars ───────────────────────────────────── */
    QScrollBar:vertical {{
        background: {t["bg_main"]};
        width: 7px;
        border-radius: 4px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t["border"]};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {t["accent"]}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: {t["bg_main"]};
        height: 7px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {t["border"]};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {t["accent"]}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    /* ── Calendar ──────────────────────────────────────── */
    QCalendarWidget {{
        min-width: 320px;
        min-height: 260px;
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
    }}
    QCalendarWidget QWidget {{
        alternate-background-color: {t["bg_panel"]};
        color: {t["text_primary"]};
    }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background-color: {t["bg_topbar"]};
        border-bottom: 1px solid {t["border"]};
    }}
    QCalendarWidget QToolButton {{
        color: {t["text_primary"]};
        background-color: transparent;
        font-weight: 700;
        border: none;
        padding: 5px;
        margin: 2px;
        border-radius: 4px;
    }}
    QCalendarWidget QToolButton:hover {{
        background-color: {t["bg_main"]};
    }}
    /* The calendar table cells */
    QCalendarWidget QTableView {{
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
        selection-background-color: {t["accent"]};
        selection-color: white;
        gridline-color: {t["border"]};
        outline: 0;
    }}
    QCalendarWidget QAbstractItemView:enabled {{
        color: {t["text_primary"]};
        background-color: {t["bg_card"]};
        selection-background-color: {t["accent"]};
        selection-color: white;
    }}
    QCalendarWidget QAbstractItemView:disabled {{
        color: {t["text_muted"]};
    }}



    QCalendarWidget QSpinBox {{
        color: {t["text_primary"]};
        background: {t["input_bg"]};
        border: 1px solid {t["border"]};
    }}
    QCalendarWidget QMenu {{
        color: {t["text_primary"]};
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
    }}
    /* ── Form fields generic ───────────────────────────── */
    QCheckBox {{
        color: {t["text_primary"]};
        spacing: 6px;
    }}
    QGroupBox {{
        border: 1px solid {t["border"]};
        border-radius: 6px;
        margin-top: 12px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        color: {t["text_primary"]};
    }}
    QRadioButton {{
        color: {t["text_primary"]};
        spacing: 6px;
    }}
    QToolTip {{
        background-color: {t["bg_card"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        padding: 4px;
        border-radius: 4px;
    }}
    QStatusBar {{
        background-color: {t["bg_topbar"]};
        color: {t["text_secondary"]};
    }}
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    /* ── Form layout label alignment ───────────────────── */
    QFormLayout QLabel {{
        color: {t["text_primary"]};
        font-weight: 500;
        font-size: 13px;
        background: transparent;
    }}
    """


