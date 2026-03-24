from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QApplication
from .terminal.employee_terminal import EmployeeTerminal
from .admin.login_dialog import AdminLoginWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AttenSync - HRMS & Terminal")

        # --- Responsive startup: 80% of the screen that the app is on ---
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(int(screen.width() * 0.82), 1440)
        h = min(int(screen.height() * 0.85), 900)
        self.resize(w, h)
        # Centre on screen
        self.move(
            screen.x() + (screen.width() - w) // 2,
            screen.y() + (screen.height() - h) // 2,
        )
        self.setMinimumSize(900, 580)

        
        # Global Stylesheet for standardizing list/table hovers
        self.setStyleSheet("""
            /* Global Styles for High Contrast & Fixes */
            QDialog {
                background-color: #ffffff;
                color: #333333;
            }
            QLabel {
                color: #333333; /* Ensure text is dark on light backgrounds */
            }
            
            /* Input Fields Standard */
            QLineEdit, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 4px;
            }

            /* ComboBox Specifics */
            QComboBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 4px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #cccccc;
                background-color: #f9f9f9;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #333333;
                selection-background-color: #2196F3;
                selection-color: white;
                border: 1px solid #cccccc;
            }
            
            /* Item Hover Effects */
            QAbstractItemView::item:hover {
                background-color: #e3f2fd; /* Light Blue */
                color: black;
            }
            QAbstractItemView::item:selected {
                background-color: #2196F3;
                color: white;
            }
            
            /* Header */
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #333333;
                padding: 4px;
                border: 1px solid #ddd;
                font-weight: bold;
            }

            /* Calendar Popup (QDateEdit calendar) */
            QCalendarWidget QWidget {
                background-color: #ffffff;
                color: #333333;
            }
            QCalendarWidget QToolButton {
                color: #333333;
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e3f2fd;
                color: #1565c0;
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
            }
            QCalendarWidget QMenu {
                color: #333333;
                background-color: #ffffff;
            }
            QCalendarWidget QSpinBox {
                color: #333333;
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 2px;
            }
            QCalendarWidget QAbstractItemView {
                color: #333333;
                background-color: #ffffff;
                selection-background-color: #2196F3;
                selection-color: #ffffff;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #333333;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #aaaaaa;
            }
        """)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Container for main content (Terminal or Admin)
        self.content_container = QWidget()
        self.content_layout = QHBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Employee Terminal is the default view
        self.terminal_widget = EmployeeTerminal()
        self.content_layout.addWidget(self.terminal_widget, stretch=1)
        
        self.main_layout.addWidget(self.content_container, stretch=1)
        
        # Bottom Bar for Admin Portal Button
        self.bottom_bar = QWidget()
        self.bottom_bar.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #ddd;")
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        
        from PyQt6.QtWidgets import QPushButton
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QCursor
        
        self.btn_admin_portal = QPushButton("⚙️ Admin Portal")
        self.btn_admin_portal.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_admin_portal.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #555; font-weight: bold; border: none; padding: 5px 10px; font-size: 14px;
            }
            QPushButton:hover { color: #333; background-color: #e0e0e0; border-radius: 4px; }
        """)
        self.btn_admin_portal.clicked.connect(self.show_admin_login)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_admin_portal)
        self.main_layout.addWidget(self.bottom_bar)
        
        self.admin_widget = None

    def show_admin_login(self):
        # Hide terminal, show admin login
        self.terminal_widget.hide()
        
        from .admin.login_dialog import AdminLoginWidget
        self.admin_widget = AdminLoginWidget(self)
        self.content_layout.addWidget(self.admin_widget, stretch=1)
        
        # Hide the bottom bar since we are in admin flow
        self.bottom_bar.hide()
        
    def switch_to_dashboard(self, dashboard_widget):
        # Remove admin login widget and replace with dashboard
        self.content_layout.removeWidget(self.admin_widget)
        self.admin_widget.deleteLater()
        
        self.admin_widget = dashboard_widget
        self.content_layout.addWidget(self.admin_widget, stretch=1)

    def logout(self):
        # Remove Dashboard
        if self.admin_widget:
            self.content_layout.removeWidget(self.admin_widget)
            self.admin_widget.deleteLater()
            self.admin_widget = None
        
        # Restore Terminal
        self.terminal_widget.show()
        self.bottom_bar.show()
