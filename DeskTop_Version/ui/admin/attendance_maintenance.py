from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDateEdit, 
                             QHeaderView, QMessageBox, QDialog, QTimeEdit, QFormLayout)
from PyQt6.QtCore import QDate, Qt
from database import get_db_session
from models import Attendance, Employee, ShortLeave
from datetime import datetime, time
from config import Config

class AttendanceMaintenance(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header with Filter
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Attendance Maintenance</h2>"))
        
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.dateChanged.connect(self.load_data)
        header.addWidget(QLabel("Date:"))
        header.addWidget(self.date_filter)
        
        header.addStretch()
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Emp ID", "Employee", "In Time", "Out Time", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)


        
    def load_data(self):
        session = get_db_session()
        selected_date = self.date_filter.date().toPyDate()
        
        # Get all attendance records for the date
        records = session.query(Attendance).filter_by(date=selected_date).all()
        
        # Also maybe list employees who are ABSENT?
        # For now, just list existing records
        
        self.table.setRowCount(0)
        for row, rec in enumerate(records):
            try:
                emp = rec.employee
                emp_id = str(emp.id) if emp else "-"
                emp_name = emp.full_name if emp else "(Unknown)"

                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(emp_id))
                self.table.setItem(row, 1, QTableWidgetItem(emp_name))
                
                time_fmt_str = Config.get_time_fmt()
                
                in_time = rec.clock_in.strftime(time_fmt_str) if rec.clock_in else "-"
                out_time = rec.clock_out.strftime(time_fmt_str) if rec.clock_out else "-"
                
                self.table.setItem(row, 2, QTableWidgetItem(in_time))
                self.table.setItem(row, 3, QTableWidgetItem(out_time))
                
                # Actions
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(2, 2, 2, 2)
                
                btn_edit = QPushButton("Edit")
                btn_edit.clicked.connect(lambda checked, r=rec: self.edit_record(r))
                action_layout.addWidget(btn_edit)
                
                btn_del = QPushButton("Delete")
                btn_del.setStyleSheet("color: red")
                btn_del.clicked.connect(lambda ch, x=rec: self.delete_record(x))
                action_layout.addWidget(btn_del)
                
                self.table.setCellWidget(row, 4, action_widget)
            except Exception as row_err:
                print(f"[AttendanceMaintenance] Error loading row {row}: {row_err}")

    def delete_record(self, record):
        confirm = QMessageBox.question(self, "Confirm", f"Delete attendance record for {record.employee.full_name}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Attendance).filter(Attendance.id == record.id).delete()
            session.commit()
            self.load_data()

    def edit_record(self, record):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Attendance - {record.employee.full_name}")
        form = QFormLayout(dialog)
        
        config = Config.load_config()
        time_fmt = Config.get_qt_time_fmt()
        
        from PyQt6.QtWidgets import QDoubleSpinBox, QCheckBox, QHBoxLayout
        
        # Clock IN
        in_layout = QHBoxLayout()
        in_cb = QCheckBox("Set")
        in_input = QTimeEdit()
        in_input.setDisplayFormat(time_fmt)
        in_input.setEnabled(False)
        in_layout.addWidget(in_cb)
        in_layout.addWidget(in_input)
        
        if record.clock_in:
            in_cb.setChecked(True)
            in_input.setEnabled(True)
            in_input.setTime(record.clock_in.time())
            
        in_cb.toggled.connect(in_input.setEnabled)
            
        # Clock OUT
        out_layout = QHBoxLayout()
        out_cb = QCheckBox("Set")
        out_input = QTimeEdit()
        out_input.setDisplayFormat(time_fmt)
        out_input.setEnabled(False)
        out_layout.addWidget(out_cb)
        out_layout.addWidget(out_input)
        
        if record.clock_out:
            out_cb.setChecked(True)
            out_input.setEnabled(True)
            out_input.setTime(record.clock_out.time())
            
        out_cb.toggled.connect(out_input.setEnabled)
        
        form.addRow("Clock In:", in_layout)
        form.addRow("Clock Out:", out_layout)
        
        # Removed dynamic calculation as duty/ot/short_leave fields are gone.
        
        btn_save = QPushButton("Update")
        btn_save.clicked.connect(lambda: self.save_record(dialog, record, 
            in_cb.isChecked(), in_input.time().toPyTime(), 
            out_cb.isChecked(), out_input.time().toPyTime()
        ))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_record(self, dialog, record, update_in, in_time, update_out, out_time):
        session = get_db_session()
        # Re-fetch to ensure attached to session
        rec = session.query(Attendance).get(record.id)
        
        # Combine date with time
        if update_in:
            rec.clock_in = datetime.combine(rec.date, in_time)
        else:
            rec.clock_in = None
            
        if update_out:
            rec.clock_out = datetime.combine(rec.date, out_time)
        else:
            rec.clock_out = None
            
        # Validation
        if rec.clock_in and rec.clock_out:
            if rec.clock_out <= rec.clock_in:
                QMessageBox.warning(dialog, "Warning", "Clock Out time must be greater than Clock In time.")
                return
            
        # Allow manual override of calculated stats
        # late_hours removed
        
        # Note: If we call calculate_daily_stats now, it might overwrite these manual changes.
        # But usually user edits happen AFTER automatic calculation.
        # If user edits times, they might want logic to re-run OR they might want to force values.
        # Given "Action button should have all field edit availity", specific manual override is implied.
        # So we do NOT call calculate_daily_stats here unless strictly necessary. 
        # But changing Time usually implies re-calc. 
        # Let's assume if user provided specific Duty/Late hours, they want those.
        
        # However, to support logical flow: Use `calculate_daily_stats` ONLY if times changed but other fields matched calculated? 
        # Complex. Let's just save what user entered. System trusts Admin.
        
        session.commit()
        dialog.accept()
        self.load_data()
