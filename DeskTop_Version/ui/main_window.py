from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QApplication, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTime, QTimer
from PyQt6.QtGui import QFont, QCursor
from .terminal.employee_terminal import EmployeeTerminal
from .admin.login_dialog import AdminLoginWidget
from ui import theme


class TopBar(QWidget):
    """Persistent top navigation bar shown at all times."""

    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
        self._build()

    def _build(self):
        self.setFixedHeight(52)
        self._refresh_bg()

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(10)

        # Brand
        brand = QLabel("AttenSync")
        brand.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        brand.setStyleSheet("color: #3F51B5; background: transparent;")
        row.addWidget(brand)

        row.addStretch()

        # Live clock
        self._lbl_clock = QLabel()
        self._lbl_clock.setStyleSheet("font-size:12px; color:#666; background:transparent; min-width:80px;")
        self._lbl_clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self._lbl_clock)
        self._tick()
        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self._tick)
        clock_timer.start(1000)



        # Admin portal (only shown in terminal view)
        self.btn_admin = QPushButton("Admin Portal")
        self.btn_admin.setFixedHeight(30)
        self.btn_admin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_admin.setStyleSheet("""
            QPushButton {
                background: #3F51B5; color: white; border: none;
                border-radius: 5px; padding: 0 14px;
                font-weight: 600; font-size: 12px;
            }
            QPushButton:hover { background: #303f9f; }
        """)
        self.btn_admin.clicked.connect(self._mw.show_admin_login)
        row.addWidget(self.btn_admin)

    def _tick(self):
        self._lbl_clock.setText(QTime.currentTime().toString("hh:mm:ss AP"))



    def _refresh_bg(self):
        t = theme.current_palette()
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {t["bg_topbar"]};
                border-bottom: 1px solid {t["border"]};
            }}
        """)

    def set_admin_mode(self, is_admin: bool):
        self.btn_admin.setVisible(not is_admin)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AttenSync - HRMS & Terminal")

        # Apply initial theme
        app = QApplication.instance()
        app.setStyle("Fusion")
        app.setStyleSheet(theme.build_stylesheet())

        # Responsive startup: 82% of screen
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(int(screen.width() * 0.82), 1440)
        h = min(int(screen.height() * 0.85), 900)
        self.resize(w, h)
        self.move(
            screen.x() + (screen.width() - w) // 2,
            screen.y() + (screen.height() - h) // 2,
        )
        self.setMinimumSize(900, 580)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        root = QVBoxLayout(self.central_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        self.top_bar = TopBar(self)
        root.addWidget(self.top_bar)

        # Thin accent line under topbar
        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3F51B5, stop:1 #03A9F4);")
        root.addWidget(sep)

        # Content area
        self.content_container = QWidget()
        self.content_layout = QHBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.terminal_widget = EmployeeTerminal()
        self.content_layout.addWidget(self.terminal_widget, stretch=1)
        root.addWidget(self.content_container, stretch=1)

        self.admin_widget = None

    def show_admin_login(self):
        self.terminal_widget.hide()
        from .admin.login_dialog import AdminLoginWidget
        self.admin_widget = AdminLoginWidget(self)
        self.content_layout.addWidget(self.admin_widget, stretch=1)
        self.top_bar.set_admin_mode(True)

    def switch_to_dashboard(self, dashboard_widget):
        self.content_layout.removeWidget(self.admin_widget)
        self.admin_widget.deleteLater()
        self.admin_widget = dashboard_widget
        self.content_layout.addWidget(self.admin_widget, stretch=1)

    def logout(self):
        if self.admin_widget:
            self.content_layout.removeWidget(self.admin_widget)
            self.admin_widget.deleteLater()
            self.admin_widget = None
        self.terminal_widget.show()
        self.top_bar.set_admin_mode(False)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            "Are you sure you want to close the HRMS system?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
