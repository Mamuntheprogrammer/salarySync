from ui.btn_styles import btn_small_edit, btn_small_delete, btn_primary, btn_neutral
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QDialog,
                             QFormLayout, QMessageBox, QComboBox,
                             QSpinBox, QDoubleSpinBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from database import get_db_session
from models import SalaryBreakdown, Employee


class SalaryBreakdownManager(QWidget):
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

        btn_add = QPushButton("＋  Add Breakdown")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_dialog(None))

        layout.addWidget(make_page_header("Salary Breakdown Manager",
                                          "Configure salary component breakdowns per employee per year",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Employee", "Year", "Valid To", "Basic", "HRA",
            "Conveyance", "Medical", "Mobile", "Transport", "Other", "Actions"
        ])
        apply_table_defaults(
            self.table,
            stretch_cols=[0],
            fixed_cols={1: 55, 2: 90, 3: 80, 4: 80, 5: 80,
                        6: 70, 7: 70, 8: 75, 9: 70, 10: 130}
        )
        cl.addWidget(self.table)
        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        self.table.setRowCount(0)
        for row, b in enumerate(session.query(SalaryBreakdown).order_by(SalaryBreakdown.year.desc()).all()):
            self.table.insertRow(row)
            emp_name = f"{b.employee.id} — {b.employee.full_name}" if b.employee else "Unknown"
            self.table.setItem(row, 0, QTableWidgetItem(emp_name))
            self.table.setItem(row, 1, QTableWidgetItem(str(b.year)))
            self.table.setItem(row, 2, QTableWidgetItem(b.valid_to.strftime("%Y-%m-%d") if b.valid_to else ""))
            self.table.setItem(row, 3, QTableWidgetItem(f"{b.basic:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{b.house_rent_allowance:,.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{b.conveyance:,.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{b.medical:,.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{b.mobile_bill:,.2f}"))
            self.table.setItem(row, 8, QTableWidgetItem(f"{b.transportation_allowance:,.2f}"))
            self.table.setItem(row, 9, QTableWidgetItem(f"{b.other_allowance:,.2f}"))

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            b1 = QPushButton("Edit")
            b1.setStyleSheet(btn_small_edit())
            b1.clicked.connect(lambda _, x=b: self.add_dialog(x))
            al.addWidget(b1)
            b2 = QPushButton("Delete")
            b2.setStyleSheet(btn_small_delete())
            b2.clicked.connect(lambda _, x=b: self.delete_breakdown(x))
            al.addWidget(b2)
            self.table.setCellWidget(row, 10, aw)

    def delete_breakdown(self, b):
        if QMessageBox.question(self, "Confirm", "Delete this salary breakdown?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(SalaryBreakdown).filter(SalaryBreakdown.id == b.id).delete()
            session.commit()
            self.load_data()

    def add_dialog(self, obj=None):
        session = get_db_session()
        employees = session.query(Employee).filter_by(is_active=True).all()

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Salary Breakdown" if obj else "Add Salary Breakdown")
        style_dialog(dialog, min_width=460)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        emp_combo = QComboBox()
        for e in employees:
            emp_combo.addItem(f"{e.id} — {e.full_name}", e.id)
        if obj and obj.employee_id:
            idx = emp_combo.findData(obj.employee_id)
            if idx >= 0:
                emp_combo.setCurrentIndex(idx)

        year_spin = QSpinBox()
        year_spin.setRange(2000, 2100)
        year_spin.setValue(obj.year if obj else QDate.currentDate().year())

        valid_to_date = QDateEdit()
        valid_to_date.setCalendarPopup(True)
        if obj and obj.valid_to:
            valid_to_date.setDate(QDate(obj.valid_to.year, obj.valid_to.month, obj.valid_to.day))
        else:
            valid_to_date.setDate(QDate(QDate.currentDate().year(), 12, 31))

        def money_spin(val=0.0):
            s = QDoubleSpinBox()
            s.setRange(0.0, 9_999_999.99)
            s.setDecimals(2)
            s.setValue(val)
            return s

        basic_spin = money_spin(obj.basic if obj else 0.0)
        hra_spin = money_spin(obj.house_rent_allowance if obj else 0.0)
        conv_spin = money_spin(obj.conveyance if obj else 0.0)
        med_spin = money_spin(obj.medical if obj else 0.0)
        mob_spin = money_spin(obj.mobile_bill if obj else 0.0)
        trans_spin = money_spin(obj.transportation_allowance if obj else 0.0)
        other_spin = money_spin(obj.other_allowance if obj else 0.0)

        total_lbl = QLabel("0.00")
        total_lbl.setStyleSheet("font-weight: 700; font-size: 14px; color: #3F51B5; background: transparent;")

        def update_total():
            total_lbl.setText(f"{sum([basic_spin.value(), hra_spin.value(), conv_spin.value(), med_spin.value(), mob_spin.value(), trans_spin.value(), other_spin.value()]):,.2f}")

        for spin in [basic_spin, hra_spin, conv_spin, med_spin, mob_spin, trans_spin, other_spin]:
            spin.valueChanged.connect(update_total)
        update_total()

        form.addRow("Employee:", emp_combo)
        form.addRow("Year:", year_spin)
        form.addRow("Valid To:", valid_to_date)
        form.addRow("Basic:", basic_spin)
        form.addRow("House Rent Allowance:", hra_spin)
        form.addRow("Conveyance:", conv_spin)
        form.addRow("Medical:", med_spin)
        form.addRow("Mobile Bill:", mob_spin)
        form.addRow("Transportation:", trans_spin)
        form.addRow("Other Allowance:", other_spin)
        form.addRow("Total:", total_lbl)

        btn_save = QPushButton("Save Breakdown")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_breakdown(dialog, obj, {
            "employee_id": emp_combo.currentData(),
            "year": year_spin.value(),
            "valid_to": valid_to_date.date().toPyDate(),
            "basic": basic_spin.value(),
            "house_rent_allowance": hra_spin.value(),
            "conveyance": conv_spin.value(),
            "medical": med_spin.value(),
            "mobile_bill": mob_spin.value(),
            "transportation_allowance": trans_spin.value(),
            "other_allowance": other_spin.value(),
        }))
        form.addRow("", btn_save)
        dialog.exec()

    def save_breakdown(self, dialog, obj, data):
        session = get_db_session()
        try:
            existing = session.query(SalaryBreakdown).filter_by(
                employee_id=data['employee_id'], year=data['year']
            ).first()
            if existing and (not obj or existing.id != obj.id):
                raise ValueError(f"A breakdown already exists for this employee in {data['year']}.")
            if obj:
                b = session.get(SalaryBreakdown, obj.id)
                for k, v in data.items():
                    setattr(b, k, v)
            else:
                session.add(SalaryBreakdown(**data))
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
