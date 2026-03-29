from ui.btn_styles import btn_primary, btn_neutral
from ui.page_helpers import make_page_header, apply_table_defaults
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QComboBox,
                             QMessageBox, QSpinBox, QFileDialog)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Employee, Company, BusinessArea
from services.payroll_service import PayrollService
from datetime import date, datetime
import csv


class PayrollModule(QWidget):
    def __init__(self):
        super().__init__()
        self.export_data = []
        self.init_ui()
        self.load_filters()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_page_header("Run Payroll",
                                          "Calculate monthly salary and save payroll records"))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        # Filter toolbar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        def labeled(text, widget):
            lbl = QLabel(text)
            lbl.setStyleSheet("background: transparent;")
            wrap = QHBoxLayout()
            wrap.setSpacing(4)
            wrap.addWidget(lbl)
            wrap.addWidget(widget)
            w = QWidget()
            w.setStyleSheet("background: transparent;")
            w.setLayout(wrap)
            return w

        self.month_sel = QComboBox()
        self.month_sel.addItems(["January", "February", "March", "April", "May", "June",
                                 "July", "August", "September", "October", "November", "December"])
        self.month_sel.setCurrentIndex(date.today().month - 1)
        self.month_sel.setMinimumWidth(110)

        self.year_sel = QSpinBox()
        self.year_sel.setRange(2020, 2030)
        self.year_sel.setValue(date.today().year)
        self.year_sel.setMinimumWidth(80)

        self.company_combo = QComboBox()
        self.company_combo.addItem("All Companies", None)
        self.company_combo.setMinimumWidth(150)
        self.company_combo.currentIndexChanged.connect(self.on_company_change)

        self.ba_combo = QComboBox()
        self.ba_combo.addItem("All Areas", None)
        self.ba_combo.setMinimumWidth(150)

        filter_row.addWidget(labeled("Month:", self.month_sel))
        filter_row.addWidget(labeled("Year:", self.year_sel))
        filter_row.addWidget(labeled("Company:", self.company_combo))
        filter_row.addWidget(labeled("Area:", self.ba_combo))
        filter_row.addStretch()

        btn_calc = QPushButton("⟳  Calculate")
        btn_calc.setStyleSheet(btn_neutral())
        btn_calc.clicked.connect(self.calculate_payroll)
        filter_row.addWidget(btn_calc)

        btn_save = QPushButton("💾  Save to DB")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(self.save_to_database)
        filter_row.addWidget(btn_save)

        btn_export = QPushButton("CSV")
        btn_export.setStyleSheet(btn_neutral())
        btn_export.clicked.connect(lambda: self.export_to_csv(
            self.export_data, self.month_sel.currentIndex() + 1, self.year_sel.value()
        ) if self.export_data else QMessageBox.warning(self, "Warning", "Calculate payroll first."))
        filter_row.addWidget(btn_export)

        cl.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Employee", "Base Salary", "Work Hrs", "Present Days",
            "Late Ded.", "Late Days Pen.", "Short Lv Ded.",
            "OT Pay", "Hol. OT Pay", "Net Salary", "Divisor", "Status"
        ])
        apply_table_defaults(
            self.table,
            stretch_cols=[0],
            fixed_cols={1: 90, 2: 75, 3: 80, 4: 80, 5: 90, 6: 85,
                        7: 75, 8: 80, 9: 90, 10: 65, 11: 70}
        )
        cl.addWidget(self.table)

        self.lbl_status = QLabel("Ready. Apply filters and click Calculate.")
        self.lbl_status.setStyleSheet("color: #55557a; font-size: 12px; background: transparent;")
        cl.addWidget(self.lbl_status)

        layout.addWidget(content, stretch=1)

    def load_filters(self):
        self.company_combo.blockSignals(True)
        session = get_db_session()
        for c in session.query(Company).all():
            self.company_combo.addItem(c.name, c.id)
        self.company_combo.blockSignals(False)

    def on_company_change(self):
        self.ba_combo.blockSignals(True)
        self.ba_combo.clear()
        self.ba_combo.addItem("All Areas", None)
        comp_id = self.company_combo.currentData()
        if comp_id:
            session = get_db_session()
            for ba in session.query(BusinessArea).filter_by(company_id=comp_id).all():
                self.ba_combo.addItem(ba.name, ba.id)
        self.ba_combo.blockSignals(False)

    def calculate_payroll(self):
        month = self.month_sel.currentIndex() + 1
        year = self.year_sel.value()
        session = get_db_session()

        query = session.query(Employee)
        if self.company_combo.currentData():
            query = query.filter_by(company_id=self.company_combo.currentData())
        if self.ba_combo.currentData():
            query = query.filter_by(business_area_id=self.ba_combo.currentData())

        employees = query.all()
        self.table.setRowCount(0)
        self.export_data = []
        self.table.itemChanged.disconnect() if self.table.receivers(self.table.itemChanged) > 0 else None

        for row, emp in enumerate(employees):
            payroll = PayrollService.calculate_salary(session, emp.id, month, year)
            if not payroll:
                continue
            payroll["employee_id"] = emp.id
            self.table.insertRow(row)

            wh = payroll["total_work_hours"]
            h, m = int(wh), int((wh - int(wh)) * 60)

            def add(col, val, editable=False, r=row):
                item = QTableWidgetItem(str(val))
                if not editable:
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, col, item)

            add(0, payroll["employee_name"])
            add(1, payroll["base_salary"], True)
            add(2, f"{h}:{m:02d}")
            add(3, payroll["present_days"])
            add(4, payroll["late_deduction"], True)
            add(5, payroll["late_days_penalty"], True)
            add(6, payroll["short_leave_deduction"], True)
            add(7, payroll["ot_pay"], True)
            add(8, payroll["holiday_ot_pay"], True)
            add(9, payroll["net_salary"], True)
            add(10, payroll.get("divisor_used", 30))
            add(11, "Draft")
            self.export_data.append(payroll)

        self.table.itemChanged.connect(self.on_item_changed)
        n = len(self.export_data)
        self.lbl_status.setText(f"Calculated {n} employee(s) for {self.month_sel.currentText()} {year}.")
        if not self.export_data:
            QMessageBox.information(self, "Info", "No data calculated for the selected filters.")

    def save_to_database(self):
        if not self.export_data:
            QMessageBox.warning(self, "Warning", "Please calculate payroll first.")
            return
        month = self.month_sel.currentIndex() + 1
        year = self.year_sel.value()
        if QMessageBox.question(self, "Confirm Save",
                                f"Save snapshot for {self.month_sel.currentText()} {year}?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) != QMessageBox.StandardButton.Yes:
            return

        updated_data = []
        for r, orig in enumerate(self.export_data):
            d = dict(orig)
            try:
                d["base_salary"] = float(self.table.item(r, 1).text())
                d["late_deduction"] = float(self.table.item(r, 4).text())
                d["ot_pay"] = float(self.table.item(r, 7).text())
                d["holiday_ot_pay"] = float(self.table.item(r, 8).text())
                d["net_salary"] = float(self.table.item(r, 9).text())
            except Exception:
                pass
            updated_data.append(d)

        session = get_db_session()
        _, msg = PayrollService.save_payroll_run(session, month, year, updated_data)
        QMessageBox.information(self, "Saved", msg)

        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            item = QTableWidgetItem("Saved")
            item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, 11, item)
        self.table.blockSignals(False)

    def on_item_changed(self, item):
        if item.column() in [1, 4, 5, 6, 7, 8]:
            self.recalculate_row(item.row())

    def recalculate_row(self, row):
        try:
            self.table.blockSignals(True)
            # Allow manual override: do not auto-recalc to avoid hidden absent deduction errors
            pass
        except Exception:
            pass
        finally:
            self.table.blockSignals(False)

    def export_to_csv(self, data, month, year):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"Payroll_{date(year, month, 1).strftime('%B%Y')}_{timestamp}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Payroll CSV", default_name, "CSV Files (*.csv)")
        if file_path:
            try:
                cols = self.table.columnCount()
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.table.horizontalHeaderItem(i).text() for i in range(cols)])
                    for r in range(self.table.rowCount()):
                        writer.writerow([
                            (self.table.item(r, c).text() if self.table.item(r, c) else "")
                            for c in range(cols)
                        ])
                QMessageBox.information(self, "Success", f"Saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
