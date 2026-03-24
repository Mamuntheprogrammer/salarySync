from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QColor


class AttendancePopupDialog(QDialog):
    """
    A polished popup shown after a successful check-in or check-out.
    Displays employee info and provides two actions:
      • Continue – closes dialog and keeps camera running
      • Done     – closes dialog and stops the camera
    """

    # Signals are communicated via the `action` attribute after exec()
    # action == 'continue'  -> keep camera on
    # action == 'done'      -> turn camera off

    def __init__(self, parent, result: dict):
        super().__init__(parent)
        self.action = "continue"  # default

        action_type = result.get("action", "check_in")
        is_checkout = action_type == "check_out"

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(480)

        # ── Outer wrapper (gives shadow room) ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        # ── Card Frame ──
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("""
            QFrame#card {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e2a3a, stop:1 #0f1923);
                border-radius: 18px;
                border: 1px solid rgba(255,255,255,0.08);
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 180))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(0)

        # ── Top accent bar ──
        accent_color = "#00C853" if not is_checkout else "#2979FF"
        accent = QFrame()
        accent.setFixedHeight(5)
        accent.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {accent_color}, stop:1 transparent);
            border-radius: 2px;
        """)
        card_layout.addWidget(accent)
        card_layout.addSpacing(18)

        # ── Icon + Action header ──
        icon_text = "✅" if not is_checkout else "🚪"
        action_label_text = "Checked In Successfully!" if not is_checkout else "Checked Out Successfully!"

        header_row = QHBoxLayout()
        icon_lbl = QLabel(icon_text)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 26))
        icon_lbl.setStyleSheet("background: transparent; color: white;")

        action_lbl = QLabel(action_label_text)
        action_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        action_lbl.setStyleSheet(f"color: {accent_color}; background: transparent;")

        header_row.addWidget(icon_lbl)
        header_row.addSpacing(12)
        header_row.addWidget(action_lbl)
        header_row.addStretch()
        card_layout.addLayout(header_row)
        card_layout.addSpacing(20)

        # ── Divider ──
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(255,255,255,0.10); border: none;")
        card_layout.addWidget(div)
        card_layout.addSpacing(18)

        # ── Info rows helper ──
        def info_row(icon: str, label: str, value: str, highlight: bool = False):
            row = QHBoxLayout()
            row.setSpacing(10)

            ico = QLabel(icon)
            ico.setFont(QFont("Segoe UI Emoji", 14))
            ico.setFixedWidth(28)
            ico.setStyleSheet("background: transparent; color: #aaa;")

            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setFixedWidth(130)
            lbl.setStyleSheet("color: #8899aa; background: transparent;")

            val_color = "#ffffff" if not highlight else accent_color
            val = QLabel(value or "—")
            val.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if highlight else QFont.Weight.Normal))
            val.setStyleSheet(f"color: {val_color}; background: transparent;")
            val.setWordWrap(True)

            row.addWidget(ico)
            row.addWidget(lbl)
            row.addWidget(val, stretch=1)
            return row

        card_layout.addLayout(info_row("🪪", "Employee ID", result.get("employee_id", "—")))
        card_layout.addSpacing(8)
        card_layout.addLayout(info_row("👤", "Name", result.get("employee_name", "—")))
        card_layout.addSpacing(8)
        card_layout.addLayout(info_row("🏢", "Business Area", result.get("business_area", "—")))
        card_layout.addSpacing(14)

        # ── Time section ──
        time_div = QFrame()
        time_div.setStyleSheet("""
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.07);
        """)
        time_layout = QVBoxLayout(time_div)
        time_layout.setContentsMargins(16, 12, 16, 12)
        time_layout.setSpacing(8)

        time_label = QLabel("🕒  Time Log")
        time_label.setFont(QFont("Segoe UI", 9))
        time_label.setStyleSheet("color: #667788; background: transparent; border: none;")
        time_layout.addWidget(time_label)

        clock_in_val = result.get("clock_in") or "—"
        clock_out_val = result.get("clock_out") or "—"
        total_hours_val = result.get("total_hours") or "—"

        time_layout.addLayout(info_row("🟢", "Check In", clock_in_val))

        if is_checkout:
            time_layout.addLayout(info_row("🔴", "Check Out", clock_out_val))
            time_layout.addSpacing(4)
            hours_row = info_row("⏱️", "Total Hours", total_hours_val, highlight=True)
            time_layout.addLayout(hours_row)

        card_layout.addWidget(time_div)
        card_layout.addSpacing(24)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_continue = QPushButton("▶  Continue")
        btn_continue.setFixedHeight(44)
        btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_continue.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_continue.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                color: #ccddee;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 10px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.14);
                color: white;
                border-color: rgba(255,255,255,0.3);
            }
            QPushButton:pressed { background: rgba(255,255,255,0.06); }
        """)
        btn_continue.clicked.connect(self._on_continue)

        btn_done = QPushButton("✔  Done")
        btn_done.setFixedHeight(44)
        btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_done.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_done.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_color}, stop:1 {"#00897B" if not is_checkout else "#1565C0"});
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {"#00E676" if not is_checkout else "#448AFF"},
                    stop:1 {"#00BFA5" if not is_checkout else "#1E88E5"});
            }}
            QPushButton:pressed {{ opacity: 0.85; }}
        """)
        btn_done.clicked.connect(self._on_done)

        btn_row.addWidget(btn_continue, stretch=1)
        btn_row.addWidget(btn_done, stretch=1)
        card_layout.addLayout(btn_row)

        outer.addWidget(card)

        # Auto-close timer (15 s default → done)
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.setInterval(15_000)
        self._auto_timer.timeout.connect(self._on_continue)  # auto-continue on timeout
        self._auto_timer.start()

    # ── Actions ──────────────────────────────────────────────────────────
    def _on_continue(self):
        self._auto_timer.stop()
        self.action = "continue"
        self.accept()

    def _on_done(self):
        self._auto_timer.stop()
        self.action = "done"
        self.accept()
