from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QDialog,
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView,
                             QComboBox, QDoubleSpinBox, QTimeEdit, QDateEdit,
                             QScrollArea)
from PyQt6.QtCore import Qt, QTime, QDate
from database import get_db_session
from models import Employee, Company, BusinessArea, Shift, Designation, DesignationSubcategory
from services.employee_service import EmployeeService
from ui.btn_styles import btn_toggle_active, btn_toggle_inactive, btn_small_edit, btn_primary, btn_neutral
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog


class EmployeeManagement(QWidget):
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

        btn_add = QPushButton("＋  Add Employee")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(self.add_employee_dialog)

        layout.addWidget(make_page_header("Employee Management",
                                          "View and manage all employees",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Company", "Area", "Shift",
            "Designation", "Salary", "Valid To", "Resign", "Status", "Actions"
        ])
        apply_table_defaults(
            self.table,
            stretch_cols=[1, 2, 3, 4, 5],
            fixed_cols={0: 50, 6: 90, 7: 90, 8: 80, 9: 70, 10: 190},
            min_section_size=50
        )
        cl.addWidget(self.table)
        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        employees = session.query(Employee).all()
        self.table.setRowCount(0)
        for row, emp in enumerate(employees):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(emp.id)))
            self.table.setItem(row, 1, QTableWidgetItem(emp.full_name))
            self.table.setItem(row, 2, QTableWidgetItem(emp.company.name if emp.company else "-"))
            self.table.setItem(row, 3, QTableWidgetItem(emp.business_area.name if emp.business_area else "-"))

            shift_name = emp.shift.name if emp.shift else ("Custom" if emp.custom_shift_start else "None")
            self.table.setItem(row, 4, QTableWidgetItem(shift_name))

            designation_str = emp.designation.name if emp.designation else "-"
            if emp.designation_subcategory:
                designation_str += f" / {emp.designation_subcategory.name}"
            self.table.setItem(row, 5, QTableWidgetItem(designation_str))
            self.table.setItem(row, 6, QTableWidgetItem(str(emp.salary_base)))
            self.table.setItem(row, 7, QTableWidgetItem(emp.valid_to.strftime("%Y-%m-%d") if emp.valid_to else "-"))
            self.table.setItem(row, 8, QTableWidgetItem(emp.resign_status if emp.resign_status else "-"))

            status_item = QTableWidgetItem("Active" if emp.is_active else "Inactive")
            status_item.setForeground(Qt.GlobalColor.darkGreen if emp.is_active else Qt.GlobalColor.red)
            self.table.setItem(row, 9, status_item)

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)

            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(btn_small_edit())
            btn_edit.clicked.connect(lambda _, e=emp: self.edit_employee_dialog(e))
            al.addWidget(btn_edit)

            btn_toggle = QPushButton("Deactivate" if emp.is_active else "Activate")
            btn_toggle.setStyleSheet(btn_toggle_inactive() if emp.is_active else btn_toggle_active())
            btn_toggle.clicked.connect(lambda _, e=emp: self.toggle_status(e))
            al.addWidget(btn_toggle)

            self.table.setCellWidget(row, 10, aw)

    def toggle_status(self, emp):
        action = "deactivate" if emp.is_active else "activate"
        if QMessageBox.question(self, "Confirm", f"Are you sure you want to {action} {emp.full_name}?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            EmployeeService.update_employee(session, emp.id, {"is_active": not emp.is_active})
            self.load_data()

    def _build_employee_form(self, dialog, emp=None):
        """Build a scrollable employee form and return (scroll_area, field_refs_dict)."""
        session = get_db_session()
        companies = session.query(Company).all()
        designations = session.query(Designation).all()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        form = QFormLayout(inner)
        form.setContentsMargins(24, 16, 24, 16)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        name_input = QLineEdit(emp.full_name if emp else "")
        name_input.setPlaceholderText("Full name")

        company_combo = QComboBox()
        ba_combo = QComboBox()
        sel_co_idx = 0
        for i, c in enumerate(companies):
            company_combo.addItem(f"{c.code} - {c.name}", c.id)
            if emp and c.id == emp.company_id:
                sel_co_idx = i
        company_combo.setCurrentIndex(sel_co_idx)

        def update_ba():
            ba_combo.clear()
            cid = company_combo.currentData()
            sel_ba = -1
            if cid:
                bas = session.query(BusinessArea).filter_by(company_id=cid).all()
                for i, ba in enumerate(bas):
                    ba_combo.addItem(f"{ba.code} - {ba.name}", ba.id)
                    if emp and ba.id == emp.business_area_id:
                        sel_ba = i
            if sel_ba >= 0:
                ba_combo.setCurrentIndex(sel_ba)

        company_combo.currentIndexChanged.connect(update_ba)
        update_ba()

        salary_input = QDoubleSpinBox()
        salary_input.setRange(0, 1_000_000)
        salary_input.setValue(emp.salary_base if emp else 50000)

        shift_combo = QComboBox()

        def refresh_shifts(current_shift_id=None):
            shift_combo.blockSignals(True)
            shift_combo.clear()
            shift_combo.addItem("None", None)
            from sqlalchemy import or_
            cid = company_combo.currentData()
            ba_id = ba_combo.currentData()
            q = session.query(Shift)
            if cid:
                q = q.filter(or_(Shift.company_id == None, Shift.company_id == cid))
            if ba_id:
                q = q.filter(or_(Shift.business_area_id == None, Shift.business_area_id == ba_id))
            sel_idx = 0
            want = current_shift_id or (emp.shift_id if emp else None)
            for i, s in enumerate(q.order_by(Shift.name).all()):
                shift_combo.addItem(f"{s.name} ({s.start_time.strftime('%I:%M %p')}-{s.end_time.strftime('%I:%M %p')})", s.id)
                if want and s.id == want:
                    sel_idx = i + 1
            shift_combo.setCurrentIndex(sel_idx)
            shift_combo.blockSignals(False)

        company_combo.currentIndexChanged.connect(lambda: refresh_shifts())
        ba_combo.currentIndexChanged.connect(lambda: refresh_shifts())
        refresh_shifts()

        custom_start = QTimeEdit()
        custom_start.setDisplayFormat("HH:mm:ss")
        custom_end = QTimeEdit()
        custom_end.setDisplayFormat("HH:mm:ss")
        if emp and emp.custom_shift_start:
            t = emp.custom_shift_start
            custom_start.setTime(QTime(t.hour, t.minute, t.second))
        if emp and emp.custom_shift_end:
            t = emp.custom_shift_end
            custom_end.setTime(QTime(t.hour, t.minute, t.second))

        def toggle_custom():
            is_custom = shift_combo.currentData() is None
            custom_start.setEnabled(is_custom)
            custom_end.setEnabled(is_custom)
        shift_combo.currentIndexChanged.connect(toggle_custom)
        toggle_custom()

        deg_combo = QComboBox()
        deg_combo.addItem("None", None)
        sel_deg = 0
        for i, d in enumerate(designations):
            deg_combo.addItem(d.name, d.id)
            if emp and emp.designation_id and d.id == emp.designation_id:
                sel_deg = i + 1
        deg_combo.setCurrentIndex(sel_deg)

        sub_combo = QComboBox()

        def update_subs():
            sub_combo.clear()
            sub_combo.addItem("None", None)
            did = deg_combo.currentData()
            if did:
                sel_sub = 0
                subs = session.query(DesignationSubcategory).filter_by(designation_id=did).all()
                for i, s in enumerate(subs):
                    sub_combo.addItem(s.name, s.id)
                    if emp and emp.designation_subcategory_id and s.id == emp.designation_subcategory_id:
                        sel_sub = i + 1
                sub_combo.setCurrentIndex(sel_sub)
        deg_combo.currentIndexChanged.connect(update_subs)
        update_subs()

        active_combo = QComboBox()
        active_combo.addItem("Active", True)
        active_combo.addItem("Inactive", False)
        active_combo.setCurrentIndex(0 if (emp is None or emp.is_active) else 1)

        valid_to_input = QDateEdit()
        valid_to_input.setCalendarPopup(True)
        valid_to_input.setDate(QDate(emp.valid_to.year, emp.valid_to.month, emp.valid_to.day) if emp and emp.valid_to else QDate(2099, 12, 31))

        resign_status_combo = QComboBox()
        for rs in ["", "Resigned", "Terminated", "Suspended", "Retired"]:
            resign_status_combo.addItem(rs if rs else "None", rs if rs else None)
        if emp and emp.resign_status:
            idx = resign_status_combo.findData(emp.resign_status)
            if idx >= 0:
                resign_status_combo.setCurrentIndex(idx)

        resign_date_input = QDateEdit()
        resign_date_input.setCalendarPopup(True)
        resign_date_input.setDate(QDate(emp.resign_date.year, emp.resign_date.month, emp.resign_date.day) if emp and emp.resign_date else QDate.currentDate())

        form.addRow("Full Name:", name_input)
        form.addRow("Company:", company_combo)
        form.addRow("Business Area:", ba_combo)
        form.addRow("Salary:", salary_input)
        form.addRow("Shift:", shift_combo)
        form.addRow("Custom Start:", custom_start)
        form.addRow("Custom End:", custom_end)
        form.addRow("Designation:", deg_combo)
        form.addRow("Subcategory:", sub_combo)
        form.addRow("Status:", active_combo)
        form.addRow("Valid To:", valid_to_input)
        form.addRow("Resign Status:", resign_status_combo)
        form.addRow("Resign Date:", resign_date_input)

        scroll.setWidget(inner)

        fields = {
            "name": name_input,
            "company": company_combo,
            "ba": ba_combo,
            "salary": salary_input,
            "shift": shift_combo,
            "custom_start": custom_start,
            "custom_end": custom_end,
            "deg": deg_combo,
            "sub": sub_combo,
            "active": active_combo,
            "valid_to": valid_to_input,
            "resign_status": resign_status_combo,
            "resign_date": resign_date_input,
        }
        return scroll, fields

    def _collect_data(self, fields):
        f = fields
        return {
            "full_name": f["name"].text(),
            "company_id": f["company"].currentData(),
            "business_area_id": f["ba"].currentData(),
            "salary_base": f["salary"].value(),
            "shift_id": f["shift"].currentData(),
            "custom_shift_start": f["custom_start"].time().toPyTime() if f["shift"].currentData() is None else None,
            "custom_shift_end": f["custom_end"].time().toPyTime() if f["shift"].currentData() is None else None,
            "designation_id": f["deg"].currentData(),
            "designation_subcategory_id": f["sub"].currentData(),
            "is_active": f["active"].currentData(),
            "valid_to": f["valid_to"].date().toPyDate(),
            "resign_status": f["resign_status"].currentData(),
            "resign_date": f["resign_date"].date().toPyDate() if f["resign_status"].currentData() else None,
        }

    def edit_employee_dialog(self, emp):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit — {emp.full_name}")
        style_dialog(dialog, min_width=520, min_height=560)

        vlay = QVBoxLayout(dialog)
        vlay.setContentsMargins(0, 0, 0, 16)
        vlay.setSpacing(0)

        scroll, fields = self._build_employee_form(dialog, emp)
        vlay.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(24, 0, 24, 0)
        btn_row.setSpacing(8)
        btn_row.addStretch()
        btn_save = QPushButton("Update Employee")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self._save_edit(dialog, emp.id, self._collect_data(fields)))
        btn_row.addWidget(btn_save)
        vlay.addLayout(btn_row)

        dialog.exec()

    def _save_edit(self, dialog, emp_id, data):
        session = get_db_session()
        try:
            EmployeeService.update_employee(session, emp_id, data)
            QMessageBox.information(dialog, "Success", "Employee updated successfully.")
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))

    def add_employee_dialog(self):
        session = get_db_session()
        if not session.query(Company).first():
            QMessageBox.warning(self, "No Company", "Please create a Company first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Employee")
        style_dialog(dialog, min_width=520, min_height=560)

        vlay = QVBoxLayout(dialog)
        vlay.setContentsMargins(0, 0, 0, 16)
        vlay.setSpacing(0)

        scroll, fields = self._build_employee_form(dialog)
        vlay.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(24, 0, 24, 0)
        btn_row.setSpacing(8)
        btn_row.addStretch()
        btn_save = QPushButton("Create Employee")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self._save_new(dialog, self._collect_data(fields)))
        btn_row.addWidget(btn_save)
        vlay.addLayout(btn_row)

        dialog.exec()

    def _save_new(self, dialog, data):
        if not data["full_name"]:
            QMessageBox.warning(dialog, "Validation", "Full name is required")
            return
        session = get_db_session()
        try:
            emp = EmployeeService.create_employee(session, data)
            QMessageBox.information(dialog, "Success", f"Employee created! ID: {emp.id}")
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
