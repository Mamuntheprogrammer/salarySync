from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QComboBox, 
                             QHeaderView, QMessageBox, QSpinBox, QFileDialog)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Employee, Company, BusinessArea, Bonus
from datetime import date, datetime
import csv

class BonusRunModule(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_filters()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Controls
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Run Bonus</h2>"))
        
        self.month_sel = QComboBox()
        self.month_sel.addItems(["January", "February", "March", "April", "May", "June", 
                                 "July", "August", "September", "October", "November", "December"])
        self.month_sel.setCurrentIndex(date.today().month - 1)
        header.addWidget(self.month_sel)
        
        self.year_sel = QSpinBox()
        self.year_sel.setRange(2020, 2030)
        self.year_sel.setValue(date.today().year)
        header.addWidget(self.year_sel)
        
        # Filters
        self.company_combo = QComboBox()
        self.company_combo.addItem("All Companies", None)
        self.company_combo.currentIndexChanged.connect(self.on_company_change)
        header.addWidget(self.company_combo)
        
        self.ba_combo = QComboBox()
        self.ba_combo.addItem("All Areas", None)
        header.addWidget(self.ba_combo)
        
        btn_calc = QPushButton("Calculate Bonus")
        btn_calc.clicked.connect(self.calculate_bonus)
        header.addWidget(btn_calc)
        
        btn_save = QPushButton("Save to Database")
        btn_save.setStyleSheet("background-color: #2e7d32; color: white;")
        btn_save.clicked.connect(self.save_to_database)
        header.addWidget(btn_save)
        
        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(self.export_csv)
        header.addWidget(btn_export)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Employee Code", "Employee Name", "Company", "Business Area", 
            "Base Salary", "Bonus Type", "Bonus Rate/Amount", "Calculated Bonus Pay", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def load_filters(self):
        self.company_combo.blockSignals(True)
        session = get_db_session()
        companies = session.query(Company).all()
        for c in companies:
            self.company_combo.addItem(c.name, c.id)
        self.company_combo.blockSignals(False)
        
    def on_company_change(self):
        self.ba_combo.blockSignals(True)
        self.ba_combo.clear()
        self.ba_combo.addItem("All Areas", None)
        
        comp_id = self.company_combo.currentData()
        if comp_id:
            session = get_db_session()
            bas = session.query(BusinessArea).filter_by(company_id=comp_id).all()
            for ba in bas:
                self.ba_combo.addItem(ba.name, ba.id)
        
        self.ba_combo.blockSignals(False)
        
    def calculate_bonus(self):
        month = self.month_sel.currentIndex() + 1
        year = self.year_sel.value()
        
        session = get_db_session()
        
        # Active Employees who potentially have bonuses
        query = session.query(Employee).filter_by(is_active=True)
        if self.company_combo.currentData():
            query = query.filter_by(company_id=self.company_combo.currentData())
        if self.ba_combo.currentData():
            query = query.filter_by(business_area_id=self.ba_combo.currentData())
            
        employees = query.all()
        self.table.setRowCount(0)
        self.export_data = [] # Format: Dict representing row
        
        row_idx = 0
        for emp in employees:
            bonuses = session.query(Bonus).filter(
                Bonus.employee_id == emp.id,
                Bonus.month == month,
                Bonus.year == year
            ).all()
            
            # Since an employee might have multiple bonuses in a month, handle sum or separate rows
            # Let's show separate rows if multiple, or summarize. 
            # The previous logic just summed them. Let's show each valid bonus record.
            
            for b in bonuses:
                self.table.insertRow(row_idx)
                
                base_salary = emp.salary_base or 0.0
                calc_val = 0.0
                type_str = ""
                rate_str = ""
                
                if b.is_percentage:
                    calc_val = (b.amount / 100.0) * base_salary
                    type_str = "Percentage"
                    rate_str = f"{b.amount}%"
                else:
                    calc_val = b.amount
                    type_str = "Fixed Amount"
                    rate_str = f"{b.amount:.2f}"
                
                comp_name = emp.company.name if emp.company else "-"
                ba_name = emp.business_area.name if emp.business_area else "-"
                
                row_data_visual = [
                    emp.attendance_code,
                    emp.full_name,
                    comp_name,
                    ba_name,
                    f"{base_salary:.2f}",
                    type_str,
                    rate_str,
                    f"{calc_val:.2f}",
                    "Draft"
                ]
                
                for col, val in enumerate(row_data_visual):
                    item = QTableWidgetItem(str(val))
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable) # Read-only
                    self.table.setItem(row_idx, col, item)
                    
                # Back-end dict for saving
                export_dict = {
                    "employee_id": emp.id,
                    "attendance_code": emp.attendance_code,
                    "full_name": emp.full_name,
                    "base_salary": base_salary,
                    "is_percentage": b.is_percentage,
                    "bonus_provided": getattr(b, 'amount', 0.0),
                    "final_bonus_pay": calc_val
                }
                self.export_data.append(export_dict)
                row_idx += 1
                
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "No Data", "No bonus records found for the selected period and filters.")
            
    def save_to_database(self):
        if not hasattr(self, 'export_data') or not self.export_data:
            QMessageBox.warning(self, "Warning", "Please calculate the bonus run first.")
            return

        month = self.month_sel.currentIndex() + 1
        year = self.year_sel.value()
        
        reply = QMessageBox.question(self, "Confirm Save", f"Save snapshot for {self.month_sel.currentText()} {year}? This preserves the historical values.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            from services.payroll_service import PayrollService
            count, msg = PayrollService.save_bonus_run(session, month, year, self.export_data)
            
            QMessageBox.information(self, "Database Saving", msg)
            
            # Change status string to "Saved"
            self.table.blockSignals(True)
            for r in range(self.table.rowCount()):
                 item = QTableWidgetItem("Saved")
                 item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                 self.table.setItem(r, 8, item)
            self.table.blockSignals(False)

    def export_csv(self):
        if not hasattr(self, 'export_data') or not self.export_data:
            QMessageBox.warning(self, "Warning", "No data to export. Calculate bonus first.")
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        month_name = self.month_sel.currentText()
        year = self.year_sel.value()
        default_name = f"BonusRun_{month_name}_{year}_{timestamp}.csv"
        
        path, _ = QFileDialog.getSaveFileName(self, "Export Bonus Run", default_name, "CSV Files (*.csv)")
        
        if path:
            try:
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write Headers
                    cols = self.table.columnCount()
                    headers = [self.table.horizontalHeaderItem(i).text() for i in range(cols-1)] # Don't export 'Status'
                    writer.writerow(headers)
                    
                    # Write Data
                    for r_dict in self.export_data:
                        # Extract visual order from dict
                        # Format ['attendance_code', 'full_name', company?, ba?, base, type, rate, calc]
                        # Actually we can just pull from table visually instead of reconstructing from dict
                        pass
                        
                    for r in range(self.table.rowCount()):
                        row_data = []
                        for c in range(cols-1):
                            item = self.table.item(r, c)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                        
                QMessageBox.information(self, "Success", f"Data exported successfully to\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data:\n{str(e)}")
