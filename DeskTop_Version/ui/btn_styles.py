"""
Centralised QPushButton stylesheet helpers.
Import and call the appropriate function for consistent button styling.

Usage:
    from ui.btn_styles import btn_primary, btn_danger, btn_small_edit, btn_small_delete
    my_btn.setStyleSheet(btn_primary())
"""


def _make(bg: str, hover: str, text: str = "white",
          padding: str = "7px 16px", font_size: str = "12px",
          border_radius: str = "5px", extra: str = "") -> str:
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {text};
            border: none;
            border-radius: {border_radius};
            padding: {padding};
            font-size: {font_size};
            font-weight: 600;
            {extra}
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {hover}; opacity: 0.85; }}
        QPushButton:disabled {{ background-color: #b0b0b0; color: #e0e0e0; }}
    """


# ── Semantic variants ────────────────────────────────────────────────────────

def btn_primary() -> str:
    """Indigo — main actions like Save, Add, Generate."""
    return _make("#3F51B5", "#303f9f")

def btn_success() -> str:
    """Green — positive actions like Import, Confirm, Approve."""
    return _make("#388E3C", "#2E7D32")

def btn_danger() -> str:
    """Red — destructive actions like Delete, Reject, Remove."""
    return _make("#D32F2F", "#B71C1C")

def btn_warning() -> str:
    """Orange — caution actions like Deactivate, Override."""
    return _make("#F57C00", "#E65100")

def btn_neutral() -> str:
    """Slate — secondary actions like Refresh, Clear, Cancel."""
    return _make("#546E7A", "#455A64")

def btn_teal() -> str:
    """Teal — distinct secondary action like Browse / Select."""
    return _make("#00897B", "#00695C")

def btn_login() -> str:
    """Large indigo — login / submit button."""
    return _make("#3F51B5", "#303f9f",
                 padding="12px 24px", font_size="14px", border_radius="6px")

# ── Small inline row buttons (Edit / Delete columns) ────────────────────────

def btn_small_edit() -> str:
    return _make("#FF9800", "#E65100",
                 padding="3px 10px", font_size="11px", border_radius="4px")

def btn_small_delete() -> str:
    return _make("#D32F2F", "#B71C1C",
                 padding="3px 10px", font_size="11px", border_radius="4px")

def btn_small_neutral() -> str:
    return _make("#546E7A", "#455A64",
                 padding="3px 10px", font_size="11px", border_radius="4px")

def btn_small_approve() -> str:
    return _make("#388E3C", "#2E7D32",
                 padding="3px 10px", font_size="11px", border_radius="4px")

def btn_small_reject() -> str:
    return _make("#D32F2F", "#B71C1C",
                 padding="3px 10px", font_size="11px", border_radius="4px")

def btn_toggle_active() -> str:
    """Green — shown when entity is active (click to deactivate)."""
    return _make("#388E3C", "#2E7D32",
                 padding="4px 10px", font_size="11px", border_radius="4px")

def btn_toggle_inactive() -> str:
    """Red — shown when entity is inactive (click to activate)."""
    return _make("#D32F2F", "#B71C1C",
                 padding="4px 10px", font_size="11px", border_radius="4px")
