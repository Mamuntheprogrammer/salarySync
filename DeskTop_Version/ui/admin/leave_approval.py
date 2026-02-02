from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QTabWidget, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from database import get_db_session
from models import LeaveRequest, ShortLeave, Employee
from services.leave_service import LeaveService
from datetime import datetime
from config import Config

class LeaveApproval(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(QLabel("<h2>Leave Approval</h2>"))
        
        # Tools
        tools = QHBoxLayout()
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_data)
        tools.addWidget(btn_refresh)
        tools.addStretch()
        layout.addLayout(tools)
        
        # Tabs
        self.tabs = QTabWidget()
        
        self.tabs.addTab(self.create_full_leave_tab(), "Full Leaves (Pending)")
        self.tabs.addTab(self.create_short_leave_tab(), "Short Leaves (Pending)")
        
        layout.addWidget(self.tabs)
        
        self.load_data()
        
    def create_full_leave_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.full_table = QTableWidget()
        self.full_table.setColumnCount(7)
        self.full_table.setHorizontalHeaderLabels([
            "ID", "Employee", "Type", "Start", "End", "Reason", "Actions"
        ])
        self.full_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.full_table)
        
        return widget

    def create_short_leave_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.short_table = QTableWidget()
        self.short_table.setColumnCount(7)
        self.short_table.setHorizontalHeaderLabels([
            "ID", "Employee", "Date", "Start", "End", "Reason", "Actions"
        ])
        self.short_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.short_table)
        
        return widget
        
    def load_data(self):
        session = get_db_session()
        
        # 1. Full Leaves
        pending_full = session.query(LeaveRequest).filter_by(status='Pending').all()
        self.tabs.setTabText(0, f"Full Leaves (Pending) ({len(pending_full)})")
        
        self.full_table.setRowCount(0)
        for row, req in enumerate(pending_full):
            self.full_table.insertRow(row)
            self.full_table.setItem(row, 0, QTableWidgetItem(str(req.id)))
            self.full_table.setItem(row, 1, QTableWidgetItem(f"{req.employee.attendance_code} - {req.employee.full_name}"))
            self.full_table.setItem(row, 2, QTableWidgetItem(req.leave_type))
            self.full_table.setItem(row, 3, QTableWidgetItem(str(req.start_date)))
            self.full_table.setItem(row, 4, QTableWidgetItem(str(req.end_date)))
            self.full_table.setItem(row, 5, QTableWidgetItem(req.reason))
            
            # Actions
            actions = QWidget()
            h = QHBoxLayout(actions)
            h.setContentsMargins(0,0,0,0)
            btn_app = QPushButton("✓")
            btn_app.setStyleSheet("color: green; font-weight: bold;")
            btn_app.clicked.connect(lambda ch, r=req: self.approve_full(r))
            
            btn_rej = QPushButton("✗")
            btn_rej.setStyleSheet("color: red; font-weight: bold;")
            btn_rej.clicked.connect(lambda ch, r=req: self.reject_full(r))
            
            h.addWidget(btn_app)
            h.addWidget(btn_rej)
            self.full_table.setCellWidget(row, 6, actions)

        # 2. Short Leaves
        pending_short = session.query(ShortLeave).filter_by(status='Pending').all()
        self.tabs.setTabText(1, f"Short Leaves (Pending) ({len(pending_short)})")
        
        self.short_table.setRowCount(0)
        for row, req in enumerate(pending_short):
            self.short_table.insertRow(row)
            self.short_table.setItem(row, 0, QTableWidgetItem(str(req.id)))
            self.short_table.setItem(row, 1, QTableWidgetItem(f"{req.employee.attendance_code} - {req.employee.full_name}"))
            self.short_table.setItem(row, 2, QTableWidgetItem(str(req.date)))
            self.short_table.setItem(row, 2, QTableWidgetItem(str(req.date)))
            
            time_fmt = Config.get_time_fmt()
            s_time = req.start_time.strftime(time_fmt)
            e_time = req.end_time.strftime(time_fmt)
            
            self.short_table.setItem(row, 3, QTableWidgetItem(s_time))
            self.short_table.setItem(row, 4, QTableWidgetItem(e_time))
            self.short_table.setItem(row, 5, QTableWidgetItem(req.reason))
            
            actions = QWidget()
            h = QHBoxLayout(actions)
            h.setContentsMargins(0,0,0,0)
            btn_app = QPushButton("✓")
            btn_app.setStyleSheet("color: green; font-weight: bold;")
            btn_app.clicked.connect(lambda ch, r=req: self.approve_short(r))
            
            btn_rej = QPushButton("✗")
            btn_rej.setStyleSheet("color: red; font-weight: bold;")
            btn_rej.clicked.connect(lambda ch, r=req: self.reject_short(r))
            
            h.addWidget(btn_app)
            h.addWidget(btn_rej)
            self.short_table.setCellWidget(row, 6, actions)

    def approve_full(self, req):
        session = get_db_session()
        res = LeaveService.approve_request(session, req.id, "admin") # Todo: current user
        QMessageBox.information(self, "Result", res['message'])
        self.load_data()
        
    def reject_full(self, req):
        session = get_db_session()
        res = LeaveService.reject_request(session, req.id, "Rejected by Admin")
        QMessageBox.information(self, "Result", res['message'])
        self.load_data()
        
    def approve_short(self, req):
        session = get_db_session()
        res = LeaveService.approve_short_leave(session, req.id)
        QMessageBox.information(self, "Result", res['message'])
        self.load_data()
        
    def reject_short(self, req):
        session = get_db_session()
        res = LeaveService.reject_short_leave(session, req.id)
        QMessageBox.information(self, "Result", res['message'])
        self.load_data()
