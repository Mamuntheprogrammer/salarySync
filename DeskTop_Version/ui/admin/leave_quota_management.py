from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView, QComboBox, QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import LeaveQuota, Company, BusinessArea
from datetime import datetime

class LeaveQuotaManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Leave Quota Management</h2>"))
        
        btn_add = QPushButton("Add Quota")
        btn_add.clicked.connect(self.add_quota_dialog)
        header.addWidget(btn_add)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Year", "Leave Type", "Quota", "Company", "Business Area", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def load_data(self):
        session = get_db_session()
        quotas = session.query(LeaveQuota).all()
        
        self.table.setRowCount(0)
        for row, q in enumerate(quotas):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(q.year)))
            self.table.setItem(row, 1, QTableWidgetItem(q.leave_type))
            self.table.setItem(row, 2, QTableWidgetItem(str(q.quota_limit)))
            
            c_name = q.company.name if q.company else "Global"
            self.table.setItem(row, 3, QTableWidgetItem(c_name))
            
            ba_name = q.business_area.name if q.business_area else "All"
            self.table.setItem(row, 4, QTableWidgetItem(ba_name))
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_delete = QPushButton("Delete")
            btn_delete.setStyleSheet("background-color: #f44336; color: white;")
            btn_delete.clicked.connect(lambda ch, x=q: self.delete_quota(x))
            action_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(row, 5, action_widget)
            
    def delete_quota(self, quota):
        confirm = QMessageBox.question(self, "Confirm", "Delete this quota?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(LeaveQuota).filter(LeaveQuota.id == quota.id).delete()
            session.commit()
            self.load_data()

    def add_quota_dialog(self):
        session = get_db_session()
        companies = session.query(Company).all()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Leave Quota")
        form = QFormLayout(dialog)
        
        year_input = QSpinBox()
        year_input.setRange(2020, 2030)
        year_input.setValue(datetime.now().year)
        
        type_input = QComboBox()
        type_input.addItems(["ShortLeave", "SickLeave", "CasualLeave", "AnnualLeave"])
        
        limit_input = QDoubleSpinBox()
        limit_input.setRange(0, 365)
        
        company_combo = QComboBox()
        company_combo.addItem("Global (All Companies)", None)
        for c in companies:
            company_combo.addItem(c.name, c.id)
            
        ba_combo = QComboBox()
        ba_combo.addItem("All Areas", None)
        
        def update_ba():
            ba_combo.clear()
            ba_combo.addItem("All Areas", None)
            cid = company_combo.currentData()
            if cid:
                bas = session.query(BusinessArea).filter_by(company_id=cid).all()
                for ba in bas:
                    ba_combo.addItem(ba.name, ba.id)
                    
        company_combo.currentIndexChanged.connect(update_ba)
        
        form.addRow("Year:", year_input)
        form.addRow("Type:", type_input)
        form.addRow("Quota Limit (Hours/Days):", limit_input)
        form.addRow("Company:", company_combo)
        form.addRow("Business Area:", ba_combo)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(lambda: self.save_quota(dialog, {
            "year": year_input.value(),
            "leave_type": type_input.currentText(),
            "quota_limit": limit_input.value(),
            "company_id": company_combo.currentData(),
            "business_area_id": ba_combo.currentData()
        }))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_quota(self, dialog, data):
        session = get_db_session()
        try:
            # Check duplicate?
            # Ideally yes, but skipping for speed unless critical.
            
            # Simple unique check: Year + Type + Company + BA
            exists = session.query(LeaveQuota).filter_by(
                year=data['year'], 
                leave_type=data['leave_type'],
                company_id=data['company_id'], 
                business_area_id=data['business_area_id']
            ).first()
            
            if exists:
                 QMessageBox.warning(dialog, "Error", "Quota already exists for this combination.")
                 return

            q = LeaveQuota(**data)
            session.add(q)
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
