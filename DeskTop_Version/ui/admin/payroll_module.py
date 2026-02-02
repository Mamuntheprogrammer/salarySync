from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QComboBox, 
                             QHeaderView, QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Employee
from services.payroll_service import PayrollService
from database import get_db_session
from models import Employee, Company, BusinessArea
from services.payroll_service import PayrollService
from datetime import date, datetime
import csv
from PyQt6.QtWidgets import QFileDialog

class PayrollModule(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_filters()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Controls
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Run Payroll</h2>"))
        
        self.month_sel = QComboBox()
        self.month_sel.addItems(["January", "February", "March", "April", "May", "June", 
                                 "July", "August", "September", "October", "November", "December"])
        self.month_sel.setCurrentIndex(date.today().month - 1)
        header.addWidget(self.month_sel)
        
        self.year_sel = QSpinBox()
        self.year_sel.setRange(2020, 2030)
        self.year_sel.setValue(date.today().year)
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
        
        btn_calc = QPushButton("Calculate Payroll")
        btn_calc.clicked.connect(self.calculate_payroll)
        header.addWidget(btn_calc)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Employee", "Base Salary", "Present Days", "Late Ded.", "Late Days Pen.", "Short Lv Ded.", "OT Pay", "Hol. OT Pay", "Net Salary", "Divisor", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def calculate_payroll(self):
        month = self.month_sel.currentIndex() + 1
        year = self.year_sel.value()
        
        session = get_db_session()
        
        # Filter Logic
        query = session.query(Employee)
        if self.company_combo.currentData():
            query = query.filter_by(company_id=self.company_combo.currentData())
        if self.ba_combo.currentData():
            query = query.filter_by(business_area_id=self.ba_combo.currentData())
            
        employees = query.all()
        
        self.table.setRowCount(0)
        
        # Prepare data for export
        export_data = []
        
        for row, emp in enumerate(employees):
            payroll = PayrollService.calculate_salary(session, emp.id, month, year)
            
            if payroll:
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(payroll["employee_name"]))
                self.table.setItem(row, 1, QTableWidgetItem(str(payroll["base_salary"])))
                self.table.setItem(row, 2, QTableWidgetItem(str(payroll["present_days"])))
                self.table.setItem(row, 3, QTableWidgetItem(str(payroll["late_deduction"])))
                self.table.setItem(row, 4, QTableWidgetItem(str(payroll["short_leave_deduction"])))
                self.table.setItem(row, 5, QTableWidgetItem(str(payroll["ot_pay"])))
                self.table.setItem(row, 6, QTableWidgetItem(str(payroll["holiday_ot_pay"])))
                self.table.setItem(row, 7, QTableWidgetItem(str(payroll["net_salary"])))
                self.table.setItem(row, 8, QTableWidgetItem("Draft"))
                
                self.table.insertRow(row)
                
                # Helper to add editable item
                def add_item(col, val, editable=False):
                    item = QTableWidgetItem(str(val))
                    if not editable:
                        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, col, item)

                add_item(0, payroll["employee_name"], False)
                add_item(1, payroll["base_salary"], True)
                add_item(2, payroll["present_days"], False)
                add_item(3, payroll["late_deduction"], True)
                add_item(4, payroll["late_days_penalty"], True)
                add_item(5, payroll["short_leave_deduction"], True)
                add_item(6, payroll["ot_pay"], True)
                add_item(7, payroll["holiday_ot_pay"], True)
                add_item(8, payroll["net_salary"], True) # Allow manual override
                add_item(9, payroll.get("divisor_used", 30), False)
                add_item(10, "Draft", False)
                
                export_data.append(payroll)
        
        self.table.itemChanged.connect(self.on_item_changed)
    
    def on_item_changed(self, item):
        # Simple logic: If any deduction/addition changes, update Net Salary?
        # But user might want to Override Net Salary directly.
        # So we should only auto-update if a component changes.
        # And if Net changes, just accept it.
        # Avoiding cyclic loops: block signals.
        
        if item.column() in [1, 3, 4, 5, 6, 7]: # Components
             self.recalculate_row(item.row())

    def recalculate_row(self, row):
        try:
             self.table.blockSignals(True)
             base = float(self.table.item(row, 1).text() or 0)
             late = float(self.table.item(row, 3).text() or 0)
             late_pen = float(self.table.item(row, 4).text() or 0)
             sl = float(self.table.item(row, 5).text() or 0)
             ot = float(self.table.item(row, 6).text() or 0)
             hol = float(self.table.item(row, 7).text() or 0)
             
             # We don't have absent deduction in column? It was part of calculation but not shown separately in table (hidden in Net?).
             # Wait, logic in service: net = gross - late - late_pen - SL - absent + OT + HolOT.
             # In table we show: Employee, Base, Present, Late, LatePen, SL, OT, HolOT, Net.
             # Absent deduction is implicit? Or missed?
             # Base Salary usually means Gross.
             # If Absent days exist, Base should be adjusted or Absent Deduction shown.
             # User didn't ask for Absent column. But Net might not match Base - Deductions + Additions if Absent is missing.
             # I should probably add Absent Deduction column for clarity if I want to recalculate correctly. 
             # For now, I'll assume Net = Base - (Late + Pen + SL) + (OT + Hol). Absent deduction is missing from the formula in UI recalculation!
             # This is risky. But user just said "update the logic considering the payroll".
             # I'll stick to manual override for Net if they want. 
             # OR I add Absent Deduction column.
             # Let's add Absent Deduction column (col index 3?)?
             # Actually, simpler: Just allow editing Net Salary directly if calculation is complex.
             # But if I change Late Deduction, Net SHOULD update. 
             # Let's calculate: Net = Previous Net + (Old Late - New Late). 
             # That requires storing old values. Complex.
             # Let's just implement: Net = Base - (Late+Pen+SL) + OT + Hol. (Ignoring Absent for now? Or fetching Absent from service logic? - Absent logic is complex).
             # Solution: Don't implement auto-recalc for now to avoid breaking hidden logic (Absent). Just allow editable fields. 
             # The user said "payrol manage must have the autority to upadate the any fields".
             # So if I update Late Deduction, Net Salary *won't* update automatically, user has to update Net Salary manually. 
             # That's safer than auto-updating wrongly.
             pass
        except:
             pass
        finally:
             self.table.blockSignals(False)
        
        # Auto-prompt for export
        if export_data:
            reply = QMessageBox.question(self, "Export", "Payroll Calculated. Do you want to save the output to Excel (CSV)?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.export_to_csv(export_data, month, year)
        else:
             QMessageBox.information(self, "Info", "No data to export.")

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

    def export_to_csv(self, data, month, year):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"Payroll_{date(year, month, 1).strftime('%B%Y')}_{timestamp}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Payroll", default_name, "CSV Files (*.csv)")
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Get Headers from Table
                    cols = self.table.columnCount()
                    headers = [self.table.horizontalHeaderItem(i).text() for i in range(cols)]
                    writer.writerow(headers)
                    
                    # Get Data from Table
                    rows = self.table.rowCount()
                    for r in range(rows):
                        row_data = []
                        for c in range(cols):
                            item = self.table.item(r, c)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                        
                QMessageBox.information(self, "Success", f"Saved to {file_path}")
                QMessageBox.information(self, "Success", f"Saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
