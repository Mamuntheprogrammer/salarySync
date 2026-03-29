from ui.btn_styles import btn_primary, btn_neutral
from ui.page_helpers import make_page_header, apply_table_defaults
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QComboBox,
                             QMessageBox, QSpinBox, QFileDialog)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Employee, Company, BusinessArea, Bonus
from datetime import date, datetime
import csv


class BonusRunModule(QWidget):
    def __init__(self):
        super().__init__()
        self.export_data = []
        self.init_ui()
        self.load_filters()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_page_header("Run Bonus",
                                          "Calculate and export bonus payouts for a selected period"))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        # Filter bar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        lbl_month = QLabel("Month:")
        lbl_month.setStyleSheet("background: transparent;")
        self.month_sel = QComboBox()
        self.month_sel.addItems(["January", "February", "March", "April", "May", "June",
                                 "July", "August", "September", "October", "November", "December"])
        self.month_sel.setCurrentIndex(date.today().month - 1)
        self.month_sel.setMinimumWidth(110)

        lbl_year = QLabel("Year:")
        lbl_year.setStyleSheet("background: transparent;")
        self.year_sel = QSpinBox()
        self.year_sel.setRange(2020, 2030)
        self.year_sel.setValue(date.today().year)
        self.year_sel.setMinimumWidth(80)

        lbl_comp = QLabel("Company:")
        lbl_comp.setStyleSheet("background: transparent;")
        self.company_combo = QComboBox()
        self.company_combo.addItem("All Companies", None)
        self.company_combo.setMinimumWidth(160)
        self.company_combo.currentIndexChanged.connect(self.on_company_change)

        lbl_ba = QLabel("Area:")
        lbl_ba.setStyleSheet("background: transparent;")
        self.ba_combo = QComboBox()
        self.ba_combo.addItem("All Areas", None)
        self.ba_combo.setMinimumWidth(160)

        filter_row.addWidget(lbl_month)
        filter_row.addWidget(self.month_sel)
        filter_row.addWidget(lbl_year)
        filter_row.addWidget(self.year_sel)
        filter_row.addWidget(lbl_comp)
        filter_row.addWidget(self.company_combo)
        filter_row.addWidget(lbl_ba)
        filter_row.addWidget(self.ba_combo)
        filter_row.addStretch()

        btn_calc = QPushButton("Calculate")
        btn_calc.setStyleSheet(btn_neutral())
        btn_calc.clicked.connect(self.calculate_bonus)
        filter_row.addWidget(btn_calc)

        btn_save = QPushButton("Save to DB")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(self.save_to_database)
        filter_row.addWidget(btn_save)

        btn_export = QPushButton("Export CSV")
        btn_export.setStyleSheet(btn_neutral())
        btn_export.clicked.connect(self.export_csv)
        filter_row.addWidget(btn_export)

        cl.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Emp ID", "Employee Name", "Company", "Business Area",
            "Base Salary", "Bonus Type", "Rate/Amount", "Calculated Bonus", "Status"
        ])
        apply_table_defaults(self.table,
                             stretch_cols=[1, 7],
                             fixed_cols={0: 60, 2: 120, 3: 120, 4: 90, 5: 90, 6: 90, 8: 80})
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

    def calculate_bonus(self):
        month = self.month_sel.currentIndex() + 1
        year = self.year_sel.value()
        session = get_db_session()

        query = session.query(Employee).filter_by(is_active=True)
        if self.company_combo.currentData():
            query = query.filter_by(company_id=self.company_combo.currentData())
        if self.ba_combo.currentData():
            query = query.filter_by(business_area_id=self.ba_combo.currentData())

        employees = query.all()
        self.table.setRowCount(0)
        self.export_data = []

        row_idx = 0
        for emp in employees:
            bonuses = session.query(Bonus).filter(
                Bonus.employee_id == emp.id,
                Bonus.month == month,
                Bonus.year == year
            ).all()
            for b in bonuses:
                base_salary = emp.salary_base or 0.0
                if b.is_percentage:
                    calc_val = (b.amount / 100.0) * base_salary
                    type_str, rate_str = "Percentage", f"{b.amount}%"
                else:
                    calc_val = b.amount
                    type_str, rate_str = "Fixed", f"{b.amount:.2f}"

                self.table.insertRow(row_idx)
                row_vals = [
                    str(emp.id), emp.full_name,
                    emp.company.name if emp.company else "-",
                    emp.business_area.name if emp.business_area else "-",
                    f"{base_salary:.2f}", type_str, rate_str,
                    f"{calc_val:.2f}", "Draft"
                ]
                for col, val in enumerate(row_vals):
                    item = QTableWidgetItem(val)
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row_idx, col, item)

                self.export_data.append({
                    "employee_id": emp.id, "emp_id": emp.id,
                    "full_name": emp.full_name, "base_salary": base_salary,
                    "is_percentage": b.is_percentage,
                    "bonus_provided": b.amount, "final_bonus_pay": calc_val
                })
                row_idx += 1

        self.lbl_status.setText(f"Calculated {row_idx} bonus record(s) for {self.month_sel.currentText()} {year}.")
        if row_idx == 0:
            QMessageBox.information(self, "No Records", "No bonus records found for the selected period and filters.")

    def save_to_database(self):
        if not self.export_data:
            QMessageBox.warning(self, "Warning", "Please calculate the bonus run first.")
            return
        month = self.month_sel.currentIndex() + 1
        year = self.year_sel.value()
        if QMessageBox.question(self, "Confirm Save",
                                f"Save bonus run snapshot for {self.month_sel.currentText()} {year}?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            from services.payroll_service import PayrollService
            _, msg = PayrollService.save_bonus_run(get_db_session(), month, year, self.export_data)
            QMessageBox.information(self, "Saved", msg)
            for r in range(self.table.rowCount()):
                item = QTableWidgetItem("Saved")
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, 8, item)

    def export_csv(self):
        if not self.export_data:
            QMessageBox.warning(self, "Warning", "No data to export. Calculate first.")
            return
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"BonusRun_{self.month_sel.currentText()}_{self.year_sel.value()}_{timestamp}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export Bonus Run", default_name, "CSV Files (*.csv)")
        if path:
            try:
                cols = self.table.columnCount()
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.table.horizontalHeaderItem(i).text() for i in range(cols - 1)])
                    for r in range(self.table.rowCount()):
                        writer.writerow([
                            (self.table.item(r, c).text() if self.table.item(r, c) else "")
                            for c in range(cols - 1)
                        ])
                QMessageBox.information(self, "Success", f"Exported to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
