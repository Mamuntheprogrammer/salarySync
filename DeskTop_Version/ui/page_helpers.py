"""
Shared UI helper utilities for AttenSync admin pages.

Usage:
    from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QHeaderView, QTableWidget, QDialog, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from ui import theme


# ── Page Header ──────────────────────────────────────────────────────────────

def make_page_header(title: str, subtitle: str = "", extra_widgets: list = None) -> QWidget:
    """
    Returns a styled header widget with a coloured left-accent bar, bold title,
    optional subtitle, and optional right-side extra widgets (e.g., buttons).

    Usage:
        header = make_page_header("Company Management", extra_widgets=[btn_add])
        layout.addWidget(header)
    """
    t = theme.current_palette()

    wrapper = QWidget()
    wrapper.setObjectName("page_header_wrapper")
    wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    wrapper.setStyleSheet(f"""
        QWidget#page_header_wrapper {{
            background-color: {t["bg_card"]};
            border-bottom: 1px solid {t["border"]};
        }}
    """)

    outer = QHBoxLayout(wrapper)
    outer.setContentsMargins(0, 0, 16, 0)
    outer.setSpacing(0)

    # Accent bar on the left
    accent_bar = QFrame()
    accent_bar.setFixedWidth(4)
    accent_bar.setStyleSheet(f"background-color: {t['accent']}; border: none;")
    outer.addWidget(accent_bar)

    # Text section
    text_col = QVBoxLayout()
    text_col.setContentsMargins(16, 12, 0, 12)
    text_col.setSpacing(2)

    lbl_title = QLabel(title)
    lbl_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
    lbl_title.setStyleSheet(f"color: {t['text_primary']}; background: transparent; border: none;")
    text_col.addWidget(lbl_title)

    if subtitle:
        lbl_sub = QLabel(subtitle)
        lbl_sub.setFont(QFont("Segoe UI", 10))
        lbl_sub.setStyleSheet(f"color: {t['text_secondary']}; background: transparent; border: none;")
        text_col.addWidget(lbl_sub)

    outer.addLayout(text_col)
    outer.addStretch()

    # Optional extra widgets (buttons etc.) on the right
    if extra_widgets:
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 8, 0, 8)
        for w in extra_widgets:
            btn_row.addWidget(w)
        outer.addLayout(btn_row)

    return wrapper


# ── Table Defaults ────────────────────────────────────────────────────────────

def apply_table_defaults(
    table: QTableWidget,
    stretch_cols: list = None,
    fixed_cols: dict = None,
    min_section_size: int = 70,
):
    """
    Applies consistent table styling:
    - Hides vertical header
    - Sets alternating row colours
    - Disables editing
    - Applies stretch / fixed sizing per column

    Args:
        table:            The QTableWidget to configure.
        stretch_cols:     List of column indices to set to Stretch mode.
                          Pass None to stretch ALL columns not in fixed_cols.
        fixed_cols:       Dict of {col_index: width_px} for Fixed columns.
        min_section_size: Minimum pixel width for any section.
    """
    hh = table.horizontalHeader()
    table.verticalHeader().hide()
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
    # Give table rows enough height so inline action buttons don't clip
    table.verticalHeader().setDefaultSectionSize(48)
    hh.setMinimumSectionSize(min_section_size)

    col_count = table.columnCount()
    fixed_cols = fixed_cols or {}
    explicit_stretch = stretch_cols is not None

    for col in range(col_count):
        if col in fixed_cols:
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(col, fixed_cols[col])
        elif explicit_stretch:
            if col in stretch_cols:
                hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        else:
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)


# ── Dialog Styling ────────────────────────────────────────────────────────────

def style_dialog(dialog: QDialog, min_width: int = 440, min_height: int = 0):
    """
    Give a QDialog consistent light-theme appearance:
    min-width, window flags, and background.
    """
    t = theme.current_palette()
    dialog.setMinimumWidth(min_width)
    if min_height:
        dialog.setMinimumHeight(min_height)
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {t["bg_card"]};
        }}
        QLabel {{
            color: {t["text_primary"]};
            font-size: 13px;
            background: transparent;
        }}
        QFormLayout QLabel {{
            color: {t["text_primary"]};
            font-weight: 500;
            min-width: 120px;
        }}
    """)


# ── Section Card ─────────────────────────────────────────────────────────────

def make_card(margins=(16, 12, 16, 12)) -> QFrame:
    """Returns a styled card QFrame for grouping content inside pages."""
    t = theme.current_palette()
    card = QFrame()
    card.setFrameShape(QFrame.Shape.StyledPanel)
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {t["bg_card"]};
            border: 1px solid {t["border"]};
            border-radius: 6px;
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(*margins)
    layout.setSpacing(10)
    return card
