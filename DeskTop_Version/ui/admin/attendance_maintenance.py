from ui.btn_styles import btn_small_edit, btn_small_delete, btn_small_neutral, btn_primary, btn_neutral
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QDateEdit,
                             QMessageBox, QDialog, QTimeEdit, QFormLayout,
                             QCheckBox)
from PyQt6.QtCore import QDate, Qt
from database import get_db_session
from models import Attendance, Employee
from datetime import datetime
from config import Config
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog


class AttendanceMaintenance(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # filter widgets go into header
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setFixedWidth(130)
        self.date_filter.dateChanged.connect(self.load_data)

        lbl_date = QLabel("Date:")
        lbl_date.setStyleSheet("background: transparent;")

        date_wrap = QWidget()
        date_wrap.setObjectName("date_wrap")
        date_wrap.setStyleSheet("QWidget#date_wrap { background: transparent; }")
        dw = QHBoxLayout(date_wrap)
        dw.setContentsMargins(0, 8, 0, 8)
        dw.setSpacing(6)
        dw.addWidget(lbl_date)
        dw.addWidget(self.date_filter)

        btn_refresh = QPushButton("⟳  Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)

        layout.addWidget(make_page_header("Attendance Maintenance",
                                          "View and edit daily attendance records",
                                          extra_widgets=[date_wrap, btn_refresh]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Emp ID", "Employee Name", "Clock In", "Clock Out", "Actions"])
        apply_table_defaults(self.table,
                             stretch_cols=[1],
                             fixed_cols={0: 70, 2: 100, 3: 100, 4: 160})
        cl.addWidget(self.table)
        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        selected_date = self.date_filter.date().toPyDate()
        records = session.query(Attendance).filter_by(date=selected_date).all()
        time_fmt = Config.get_time_fmt()

        self.table.setRowCount(0)
        for row, rec in enumerate(records):
            try:
                emp = rec.employee
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(emp.id) if emp else "-"))
                self.table.setItem(row, 1, QTableWidgetItem(emp.full_name if emp else "(Unknown)"))
                self.table.setItem(row, 2, QTableWidgetItem(rec.clock_in.strftime(time_fmt) if rec.clock_in else "-"))
                self.table.setItem(row, 3, QTableWidgetItem(rec.clock_out.strftime(time_fmt) if rec.clock_out else "-"))

                aw = QWidget()
                aw.setStyleSheet("background: transparent;")
                al = QHBoxLayout(aw)
                al.setContentsMargins(4, 2, 4, 2)
                al.setSpacing(4)

                btn_edit = QPushButton("Edit")
                btn_edit.setStyleSheet(btn_small_edit())
                btn_edit.clicked.connect(lambda _, r=rec: self.edit_record(r))
                al.addWidget(btn_edit)

                btn_del = QPushButton("Delete")
                btn_del.setStyleSheet(btn_small_delete())
                btn_del.clicked.connect(lambda _, r=rec: self.delete_record(r))
                al.addWidget(btn_del)

                self.table.setCellWidget(row, 4, aw)
            except Exception as e:
                print(f"[AttendanceMaintenance] row error: {e}")

    def delete_record(self, record):
        emp_name = record.employee.full_name if record.employee else "this record"
        if QMessageBox.question(self, "Confirm",
                                f"Delete attendance record for {emp_name}?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Attendance).filter(Attendance.id == record.id).delete()
            session.commit()
            self.load_data()

    def edit_record(self, record):
        emp_name = record.employee.full_name if record.employee else "Unknown"
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Attendance — {emp_name}")
        style_dialog(dialog, min_width=420)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        time_fmt = Config.get_qt_time_fmt()

        # Clock In
        in_row = QHBoxLayout()
        in_cb = QCheckBox("Set")
        in_input = QTimeEdit()
        in_input.setDisplayFormat(time_fmt)
        in_input.setEnabled(False)
        if record.clock_in:
            in_cb.setChecked(True)
            in_input.setEnabled(True)
            in_input.setTime(record.clock_in.time())
        in_cb.toggled.connect(in_input.setEnabled)
        in_row.addWidget(in_cb)
        in_row.addWidget(in_input)

        # Clock Out
        out_row = QHBoxLayout()
        out_cb = QCheckBox("Set")
        out_input = QTimeEdit()
        out_input.setDisplayFormat(time_fmt)
        out_input.setEnabled(False)
        if record.clock_out:
            out_cb.setChecked(True)
            out_input.setEnabled(True)
            out_input.setTime(record.clock_out.time())
        out_cb.toggled.connect(out_input.setEnabled)
        out_row.addWidget(out_cb)
        out_row.addWidget(out_input)

        form.addRow("Clock In:", in_row)
        form.addRow("Clock Out:", out_row)

        btn_save = QPushButton("Update Record")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_record(
            dialog, record,
            in_cb.isChecked(), in_input.time().toPyTime(),
            out_cb.isChecked(), out_input.time().toPyTime()
        ))
        form.addRow("", btn_save)
        dialog.exec()

    def save_record(self, dialog, record, update_in, in_time, update_out, out_time):
        session = get_db_session()
        rec = session.query(Attendance).get(record.id)
        rec.clock_in = datetime.combine(rec.date, in_time) if update_in else None
        rec.clock_out = datetime.combine(rec.date, out_time) if update_out else None
        if rec.clock_in and rec.clock_out and rec.clock_out <= rec.clock_in:
            QMessageBox.warning(dialog, "Validation", "Clock Out must be after Clock In.")
            return
        session.commit()
        dialog.accept()
        self.load_data()
