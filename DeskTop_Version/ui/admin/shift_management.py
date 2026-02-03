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
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)
        
        btn_add = QPushButton("Add Shift")
        btn_add.clicked.connect(lambda: self.add_shift_dialog(None))
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Start Time", "End Time", "Late Allowance (min)", "Action"])
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
            
            # Action
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda ch, x=shift: self.add_shift_dialog(x))
            action_layout.addWidget(btn_edit)
            
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet("color: red")
            btn_del.clicked.connect(lambda ch, x=shift: self.delete_shift(x))
            action_layout.addWidget(btn_del)
            
            self.table.setCellWidget(row, 4, action_widget)
            
    def delete_shift(self, shift):
        confirm = QMessageBox.question(self, "Confirm", f"Delete shift '{shift.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Shift).filter(Shift.id == shift.id).delete()
            session.commit()
            self.load_data()

    def add_shift_dialog(self, shift_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Shift" if shift_obj else "Add Shift")
        form = QFormLayout(dialog)
        
        name_input = QLineEdit()
        if shift_obj: name_input.setText(shift_obj.name)
        
        # Get Time Format
        time_fmt = Config.get_qt_time_fmt()

        start_input = QTimeEdit()
        start_input.setDisplayFormat(time_fmt)
        if shift_obj:
            start_input.setTime(QTime(shift_obj.start_time.hour, shift_obj.start_time.minute))
        else:
            start_input.setTime(QTime(9, 0))
        
        end_input = QTimeEdit()
        end_input.setDisplayFormat(time_fmt)
        if shift_obj:
            end_input.setTime(QTime(shift_obj.end_time.hour, shift_obj.end_time.minute))
        else:
            end_input.setTime(QTime(17, 0))
        
        allowance_input = QSpinBox()
        allowance_input.setRange(0, 120)
        allowance_input.setValue(shift_obj.late_allowance_minutes if shift_obj else 15)
        
        form.addRow("Shift Name:", name_input)
        form.addRow("Start Time:", start_input)
        form.addRow("End Time:", end_input)
        form.addRow("Late Allowance (min):", allowance_input)
        
        btn_save = QPushButton("Save Shift")
        btn_save.clicked.connect(lambda: self.save_shift(dialog, 
            shift_obj,
            name_input.text(), 
            start_input.time().toPyTime(), 
            end_input.time().toPyTime(),
            allowance_input.value()
        ))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_shift(self, dialog, shift_obj, name, start, end, allowance):
        if not name:
             QMessageBox.warning(dialog, "Error", "Name required")
             return
             
        session = get_db_session()
        try:
            if shift_obj:
                s = session.get(Shift, shift_obj.id)
                s.name = name
                s.start_time = start
                s.end_time = end
                s.late_allowance_minutes = allowance
                session.commit()
            else:
                ShiftService.create_shift(session, name, start, end, allowance)
                
            dialog.accept()
            self.load_data()
        except Exception as e:
             QMessageBox.critical(dialog, "Error", str(e))
