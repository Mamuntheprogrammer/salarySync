from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QFrame
from .terminal.employee_terminal import EmployeeTerminal
from .admin.login_dialog import AdminLoginWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AttenSync - HRMS & Terminal")
        self.resize(1000, 600)
        
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
        
        self.layout = QHBoxLayout(self.central_widget)
        
        # Left Side: Employee Terminal
        self.terminal_widget = EmployeeTerminal()
        self.layout.addWidget(self.terminal_widget, stretch=1)
        
        # Vertical Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)
        
        # Right Side: Admin Login
        self.admin_widget = AdminLoginWidget(self)
        self.layout.addWidget(self.admin_widget, stretch=1)
        
    def switch_to_dashboard(self, dashboard_widget):
        # Remove admin login widget and replace with dashboard
        self.layout.removeWidget(self.admin_widget)
        self.admin_widget.deleteLater()
        
        self.admin_widget = dashboard_widget
        self.layout.addWidget(self.admin_widget, stretch=4) # Give more space to dashboard
        
        # Hide terminal if needed, or keep it on the side?
        # User requirement says "Landing page" has split screen.
        # Usually admin dashboard takes full screen.
        # Let's hide the terminal and line when admin logs in to give full space.
        self.terminal_widget.hide()
        self.layout.itemAt(1).widget().hide() # Hide line

    def logout(self):
        # 1. Remove Dashboard
        self.layout.removeWidget(self.admin_widget)
        self.admin_widget.deleteLater()
        
        # 2. Restore Admin Login
        self.admin_widget = AdminLoginWidget(self)
        self.layout.addWidget(self.admin_widget, stretch=1)
        
        # 3. Show Terminal & Line
        self.terminal_widget.show()
        self.layout.itemAt(1).widget().show() # Show line
