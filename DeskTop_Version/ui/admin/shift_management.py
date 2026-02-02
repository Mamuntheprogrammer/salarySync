from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView, QTimeEdit, QSpinBox)
from PyQt6.QtCore import QTime
from database import get_db_session
from models import Shift
from services.shift_service import ShiftService
from config import Config

class ShiftManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Shift Management</h2>"))
        
        btn_add = QPushButton("Add Shift")
        btn_add.clicked.connect(self.add_shift_dialog)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Start Time", "End Time", "Late Allowance (min)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def load_data(self):
        session = get_db_session()
        shifts = session.query(Shift).all()
        
        self.table.setRowCount(0)
        for row, shift in enumerate(shifts):
            self.table.insertRow(row)
            time_fmt_str = Config.get_time_fmt()
            
            self.table.setItem(row, 0, QTableWidgetItem(shift.name))
            self.table.setItem(row, 1, QTableWidgetItem(shift.start_time.strftime(time_fmt_str)))
            self.table.setItem(row, 2, QTableWidgetItem(shift.end_time.strftime(time_fmt_str)))
            self.table.setItem(row, 3, QTableWidgetItem(str(shift.late_allowance_minutes)))

    def add_shift_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Shift")
        form = QFormLayout(dialog)
        
        name_input = QLineEdit()
        
        # Get Time Format
        # Get Time Format
        time_fmt = Config.get_qt_time_fmt()

        start_input = QTimeEdit()
        start_input.setDisplayFormat(time_fmt)
        start_input.setTime(QTime(9, 0))
        
        end_input = QTimeEdit()
        end_input.setDisplayFormat(time_fmt)
        end_input.setTime(QTime(17, 0))
        
        allowance_input = QSpinBox()
        allowance_input.setRange(0, 120)
        allowance_input.setValue(15)
        
        form.addRow("Shift Name:", name_input)
        form.addRow("Start Time:", start_input)
        form.addRow("End Time:", end_input)
        form.addRow("Late Allowance (min):", allowance_input)
        
        btn_save = QPushButton("Save Shift")
        btn_save.clicked.connect(lambda: self.save_shift(dialog, 
            name_input.text(), 
            start_input.time().toPyTime(), 
            end_input.time().toPyTime(),
            allowance_input.value()
        ))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_shift(self, dialog, name, start, end, allowance):
        if not name:
             QMessageBox.warning(dialog, "Error", "Name required")
             return
             
        session = get_db_session()
        try:
            ShiftService.create_shift(session, name, start, end, allowance)
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
