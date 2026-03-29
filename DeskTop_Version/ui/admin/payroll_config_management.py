from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFormLayout, QMessageBox, QDoubleSpinBox,
                             QCheckBox, QComboBox, QSpinBox, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import PayrollConfig, Company
from ui.btn_styles import btn_primary, btn_neutral
from ui.page_helpers import make_page_header
from config import Config


class PayrollConfigManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_companies()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_page_header("Payroll Configuration",
                                          "Set overtime, late deduction and calculation rules per company"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(20, 16, 20, 24)
        inner_layout.setSpacing(16)

        # Company scope selector
        scope_group = QGroupBox("Scope")
        scope_form = QFormLayout(scope_group)
        scope_form.setSpacing(10)
        scope_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.comp_select = QComboBox()
        self.comp_select.addItem("Global Defaults", None)
        self.comp_select.currentIndexChanged.connect(self.load_config)
        scope_form.addRow("Apply To:", self.comp_select)
        inner_layout.addWidget(scope_group)

        # Rates group
        rates_group = QGroupBox("Rate Multipliers")
        rates_form = QFormLayout(rates_group)
        rates_form.setSpacing(10)
        rates_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

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

        rates_form.addRow("Overtime Rate (×Hourly):", self.ot_rate)
        rates_form.addRow("Holiday OT Rate (×Hourly):", self.hol_ot_rate)
        rates_form.addRow("Late Deduction (×Hourly):", self.late_rate)
        rates_form.addRow("Short Leave Deduction (×Hourly):", self.sl_rate)
        inner_layout.addWidget(rates_group)

        # Calculation rules group
        calc_group = QGroupBox("Calculation Rules")
        calc_form = QFormLayout(calc_group)
        calc_form.setSpacing(10)
        calc_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.late_penalty_days = QSpinBox()
        self.late_penalty_days.setRange(0, 30)
        self.late_penalty_days.setValue(3)
        self.late_penalty_days.setSuffix(" days late = 1 day salary deduction")

        self.calc_on_present = QCheckBox("Calculate salary based on present days (daily rate)")
        self.calc_on_present.setChecked(True)

        self.use_actual_days = QCheckBox("Use actual days in month (28/30/31)")
        self.use_actual_days.toggled.connect(self.toggle_days_input)

        self.days_in_month = QSpinBox()
        self.days_in_month.setRange(20, 31)
        self.days_in_month.setValue(30)

        calc_form.addRow("Late Days Penalty Rule:", self.late_penalty_days)
        calc_form.addRow("", self.calc_on_present)
        calc_form.addRow("", self.use_actual_days)
        calc_form.addRow("Days in Month Divisor:", self.days_in_month)
        inner_layout.addWidget(calc_group)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton("Save Configuration")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(self.save_config)
        btn_row.addWidget(btn_save)
        inner_layout.addLayout(btn_row)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll, stretch=1)

    def load_companies(self):
        self.comp_select.blockSignals(True)
        session = get_db_session()
        for c in session.query(Company).all():
            self.comp_select.addItem(c.name, c.id)
        self.comp_select.blockSignals(False)
        self.load_config()

    def toggle_days_input(self, checked):
        self.days_in_month.setEnabled(not checked)

    def load_config(self):
        session = get_db_session()
        comp_id = self.comp_select.currentData()
        config = session.query(PayrollConfig).filter_by(company_id=comp_id).first()
        if config:
            self.ot_rate.setValue(config.ot_rate_multiplier)
            self.hol_ot_rate.setValue(config.holiday_ot_rate_multiplier)
            self.late_rate.setValue(config.late_deduction_multiplier)
            self.sl_rate.setValue(config.short_leave_deduction_multiplier)
            self.late_penalty_days.setValue(getattr(config, 'late_days_penalty_threshold', 3))
            self.calc_on_present.setChecked(config.calculate_salary_on_present_days)
            self.use_actual_days.setChecked(getattr(config, 'use_actual_days_in_month', False))
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
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
