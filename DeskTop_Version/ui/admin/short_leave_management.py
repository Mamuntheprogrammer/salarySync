from ui.btn_styles import btn_small_edit, btn_small_delete, btn_primary, btn_neutral
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog,
                             QFormLayout, QMessageBox, QComboBox,
                             QDateEdit, QTimeEdit, QLineEdit)
from PyQt6.QtCore import Qt, QDate, QTime
from database import get_db_session
from models import ShortLeave, Employee
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog


class ShortLeaveManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        btn_refresh = QPushButton("⟳  Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)

        btn_add = QPushButton("＋  Add Short Leave")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_dialog(None))

        layout.addWidget(make_page_header("Short Leave Manager",
                                          "Manage short leave requests",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date", "Employee", "Start", "End", "Reason", "Status", "Actions"])
        apply_table_defaults(self.table,
                             stretch_cols=[1, 4],
                             fixed_cols={0: 90, 2: 80, 3: 80, 5: 80, 6: 140})
        cl.addWidget(self.table)
        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        self.table.setRowCount(0)
        for row, l in enumerate(session.query(ShortLeave).order_by(ShortLeave.date.desc()).all()):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(l.date.strftime("%Y-%m-%d")))
            emp_name = f"{l.employee.id} — {l.employee.full_name}" if l.employee else "Unknown"
            self.table.setItem(row, 1, QTableWidgetItem(emp_name))
            self.table.setItem(row, 2, QTableWidgetItem(l.start_time.strftime("%H:%M")))
            self.table.setItem(row, 3, QTableWidgetItem(l.end_time.strftime("%H:%M")))
            self.table.setItem(row, 4, QTableWidgetItem(l.reason or ""))
            self.table.setItem(row, 5, QTableWidgetItem(l.status))

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            b1 = QPushButton("Edit")
            b1.setStyleSheet(btn_small_edit())
            b1.clicked.connect(lambda _, x=l: self.add_dialog(x))
            al.addWidget(b1)
            b2 = QPushButton("Delete")
            b2.setStyleSheet(btn_small_delete())
            b2.clicked.connect(lambda _, x=l: self.delete_leave(x))
            al.addWidget(b2)
            self.table.setCellWidget(row, 6, aw)

    def delete_leave(self, leave):
        if QMessageBox.question(self, "Confirm", "Delete this short leave record?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(ShortLeave).filter(ShortLeave.id == leave.id).delete()
            session.commit()
            self.load_data()

    def add_dialog(self, leave_obj=None):
        session = get_db_session()
        employees = session.query(Employee).filter_by(is_active=True).all()

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Short Leave" if leave_obj else "Add Short Leave")
        style_dialog(dialog, min_width=420)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        emp_combo = QComboBox()
        for e in employees:
            emp_combo.addItem(f"{e.id} — {e.full_name}", e.id)
        if leave_obj and leave_obj.employee_id:
            idx = emp_combo.findData(leave_obj.employee_id)
            if idx >= 0:
                emp_combo.setCurrentIndex(idx)

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(leave_obj.date if leave_obj else QDate.currentDate())

        start_input = QTimeEdit()
        start_input.setTime(QTime(leave_obj.start_time.hour, leave_obj.start_time.minute) if leave_obj else QTime.currentTime())

        end_input = QTimeEdit()
        end_input.setTime(QTime(leave_obj.end_time.hour, leave_obj.end_time.minute) if leave_obj else QTime.currentTime().addSecs(3600))

        reason_input = QLineEdit(leave_obj.reason or "" if leave_obj else "")
        reason_input.setPlaceholderText("Reason for short leave")

        status_combo = QComboBox()
        status_combo.addItems(["Pending", "Approved", "Rejected"])
        if leave_obj:
            status_combo.setCurrentText(leave_obj.status)

        form.addRow("Employee:", emp_combo)
        form.addRow("Date:", date_input)
        form.addRow("Start Time:", start_input)
        form.addRow("End Time:", end_input)
        form.addRow("Reason:", reason_input)
        form.addRow("Status:", status_combo)

        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_leave(dialog, leave_obj, {
            "employee_id": emp_combo.currentData(),
            "date": date_input.date().toPyDate(),
            "start_time": start_input.time().toPyTime(),
            "end_time": end_input.time().toPyTime(),
            "reason": reason_input.text(),
            "status": status_combo.currentText()
        }))
        form.addRow("", btn_save)
        dialog.exec()

    def save_leave(self, dialog, leave_obj, data):
        session = get_db_session()
        try:
            if leave_obj:
                l = session.get(ShortLeave, leave_obj.id)
                for k, v in data.items():
                    setattr(l, k, v)
            else:
                session.add(ShortLeave(**data))
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
