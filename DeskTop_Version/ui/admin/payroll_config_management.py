from ui.custom_widgets import make_input_group
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFormLayout, QMessageBox, QDoubleSpinBox, QCheckBox, QComboBox, QSpinBox)
from database import get_db_session
from models import PayrollConfig, Company
from ui.btn_styles import btn_primary
from config import Config

class PayrollConfigManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_companies()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Payroll Configuration Manager</h2>"))
        layout.addLayout(header)
        
        # Company Selection
        self.comp_select = QComboBox()
        self.comp_select.addItem("Global Defaults", None)
        self.comp_select.currentIndexChanged.connect(self.load_config)
        
        form_layout = QFormLayout()
        form_layout.addRow(make_input_group("Select Scope:", self.comp_select))
        
        # Inputs
        self.ot_rate = QDoubleSpinBox()
        self.ot_rate.setRange(1.0, 5.0)
        self.ot_rate.setSingleStep(0.1)
        self.ot_rate.setValue(1.5)
        
        self.hol_ot_rate = QDoubleSpinBox()
        self.hol_ot_rate.setRange(1.0, 5.0)
        self.hol_ot_rate.setSingleStep(0.1)
        self.hol_ot_rate.setValue(2.0)
        
        self.late_rate = QDoubleSpinBox()
        self.late_rate.setRange(0.0, 5.0)
        self.late_rate.setSingleStep(0.1)
        self.late_rate.setValue(1.0)
        
        self.sl_rate = QDoubleSpinBox()
        self.sl_rate.setRange(0.0, 5.0)
        self.sl_rate.setSingleStep(0.1)
        self.sl_rate.setValue(1.0)

        self.late_penalty_days = QSpinBox()
        self.late_penalty_days.setRange(0, 30)
        self.late_penalty_days.setValue(3)
        self.late_penalty_days.setSuffix(" Days Late = 1 Day Salary Deduction")
        
        self.calc_on_present = QCheckBox("Calculate Salary based on Present Days (Daily Rate)")
        self.calc_on_present.setChecked(True)
        
        self.use_actual_days = QCheckBox("Use Actual Days in Month (e.g. 28, 30, 31)")
        self.use_actual_days.toggled.connect(self.toggle_days_input)
        
        self.days_in_month = QSpinBox()
        self.days_in_month.setRange(20, 31)
        self.days_in_month.setValue(30)
        
        # Layout
        form_layout.addRow(make_input_group("Overtime Rate (x Hourly):", self.ot_rate))
        form_layout.addRow(make_input_group("Holiday OT Rate (x Hourly):", self.hol_ot_rate))
        form_layout.addRow(make_input_group("Late Deduction (x Hourly):", self.late_rate))
        form_layout.addRow(make_input_group("Short Leave Deduction (x Hourly):", self.sl_rate))
        form_layout.addRow(make_input_group("Late Days Penalty Rule:", self.late_penalty_days))
        form_layout.addRow(make_input_group("Calculation Mode:", self.calc_on_present))
        form_layout.addRow(make_input_group("Divisor Mode:", self.use_actual_days))
        form_layout.addRow(make_input_group("Days in Month Divisor:", self.days_in_month))
        
        layout.addLayout(form_layout)
        
        # Save Btn
        btn_save = QPushButton("Save Configuration")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)
        
        layout.addStretch()
        
    def load_companies(self):
        self.comp_select.blockSignals(True)
        session = get_db_session()
        companies = session.query(Company).all()
        for c in companies:
            self.comp_select.addItem(c.name, c.id)
        self.comp_select.blockSignals(False)
        self.load_config()
        
    def toggle_days_input(self, checked):
        self.days_in_month.setEnabled(not checked)

    def load_config(self):
        # ... (rest of load logic)
        session = get_db_session()
        comp_id = self.comp_select.currentData()
        config = session.query(PayrollConfig).filter_by(company_id=comp_id).first()
        
        if config:
            self.ot_rate.setValue(config.ot_rate_multiplier)
            self.hol_ot_rate.setValue(config.holiday_ot_rate_multiplier)
            self.late_rate.setValue(config.late_deduction_multiplier)
            self.sl_rate.setValue(config.short_leave_deduction_multiplier)
            self.late_penalty_days.setValue(config.late_days_penalty_threshold if hasattr(config, 'late_days_penalty_threshold') else 0)
            self.calc_on_present.setChecked(config.calculate_salary_on_present_days)
            self.use_actual_days.setChecked(config.use_actual_days_in_month if hasattr(config, 'use_actual_days_in_month') else False)
            self.days_in_month.setValue(config.days_in_month_calculation)
        else:
            self.ot_rate.setValue(1.5)
            self.hol_ot_rate.setValue(2.0)
            self.late_rate.setValue(1.0)
            self.sl_rate.setValue(1.0)
            self.late_penalty_days.setValue(3)
            self.calc_on_present.setChecked(True)
            self.use_actual_days.setChecked(False)
            self.days_in_month.setValue(30)
        self.toggle_days_input(self.use_actual_days.isChecked())

    def save_config(self):
        session = get_db_session()
        comp_id = self.comp_select.currentData()
        
        config = session.query(PayrollConfig).filter_by(company_id=comp_id).first()
        
        if not config:
            config = PayrollConfig(company_id=comp_id)
            session.add(config)
            
        config.ot_rate_multiplier = self.ot_rate.value()
        config.holiday_ot_rate_multiplier = self.hol_ot_rate.value()
        config.late_deduction_multiplier = self.late_rate.value()
        config.short_leave_deduction_multiplier = self.sl_rate.value()
        config.late_days_penalty_threshold = self.late_penalty_days.value()
        config.calculate_salary_on_present_days = self.calc_on_present.isChecked()
        config.use_actual_days_in_month = self.use_actual_days.isChecked()
        config.days_in_month_calculation = self.days_in_month.value()
        
        try:
            session.commit()
            QMessageBox.information(self, "Success", "Configuration saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
