from ui.btn_styles import btn_small_delete, btn_primary, btn_small_edit, btn_neutral
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog,
                             QFormLayout, QMessageBox, QComboBox,
                             QLineEdit, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import LeaveQuota, Company, BusinessArea
from datetime import datetime
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog


class LeaveQuotaManagement(QWidget):
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

        btn_add = QPushButton("＋  Add Quota")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(self.add_quota_dialog)

        layout.addWidget(make_page_header("Leave Quota Manager",
                                          "Set annual leave quotas per leave type and company",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Year", "Leave Type", "Quota", "Company", "Business Area", "Actions"])
        apply_table_defaults(self.table,
                             stretch_cols=[1, 3, 4],
                             fixed_cols={0: 60, 2: 70, 5: 140})
        cl.addWidget(self.table)
        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        self.table.setRowCount(0)
        for row, q in enumerate(session.query(LeaveQuota).all()):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(q.year)))
            self.table.setItem(row, 1, QTableWidgetItem(q.leave_type))
            self.table.setItem(row, 2, QTableWidgetItem(str(q.quota_limit)))
            self.table.setItem(row, 3, QTableWidgetItem(q.company.name if q.company else "Global"))
            self.table.setItem(row, 4, QTableWidgetItem(q.business_area.name if q.business_area else "All"))

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            b1 = QPushButton("Edit")
            b1.setStyleSheet(btn_small_edit())
            b1.clicked.connect(lambda _, x=q: self.add_quota_dialog(x))
            al.addWidget(b1)
            b2 = QPushButton("Delete")
            b2.setStyleSheet(btn_small_delete())
            b2.clicked.connect(lambda _, x=q: self.delete_quota(x))
            al.addWidget(b2)
            self.table.setCellWidget(row, 5, aw)

    def delete_quota(self, quota):
        if QMessageBox.question(self, "Confirm", "Delete this leave quota?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(LeaveQuota).filter(LeaveQuota.id == quota.id).delete()
            session.commit()
            self.load_data()

    def add_quota_dialog(self, quota=None):
        session = get_db_session()
        companies = session.query(Company).all()

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Leave Quota" if quota else "Add Leave Quota")
        style_dialog(dialog, min_width=440)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        year_input = QSpinBox()
        year_input.setRange(2020, 2035)
        year_input.setValue(quota.year if quota else datetime.now().year)

        type_input = QComboBox()
        type_input.addItems(["ShortLeave", "SickLeave", "CasualLeave", "AnnualLeave"])
        if quota:
            type_input.setCurrentText(quota.leave_type)

        limit_input = QDoubleSpinBox()
        limit_input.setRange(0, 365)
        limit_input.setValue(quota.quota_limit if quota else 0)

        company_combo = QComboBox()
        company_combo.addItem("Global (All Companies)", None)
        for c in companies:
            company_combo.addItem(c.name, c.id)
        if quota:
            idx = company_combo.findData(quota.company_id)
            if idx >= 0:
                company_combo.setCurrentIndex(idx)

        ba_combo = QComboBox()

        def update_ba():
            ba_combo.clear()
            ba_combo.addItem("All Areas", None)
            cid = company_combo.currentData()
            if cid:
                for ba in session.query(BusinessArea).filter_by(company_id=cid).all():
                    ba_combo.addItem(ba.name, ba.id)

        company_combo.currentIndexChanged.connect(update_ba)
        update_ba()
        if quota:
            idx = ba_combo.findData(quota.business_area_id)
            if idx >= 0:
                ba_combo.setCurrentIndex(idx)

        form.addRow("Year:", year_input)
        form.addRow("Leave Type:", type_input)
        form.addRow("Quota Limit:", limit_input)
        form.addRow("Company:", company_combo)
        form.addRow("Business Area:", ba_combo)

        btn_save = QPushButton("Save Quota")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_quota(dialog, {
            "id": quota.id if quota else None,
            "year": year_input.value(),
            "leave_type": type_input.currentText(),
            "quota_limit": limit_input.value(),
            "company_id": company_combo.currentData(),
            "business_area_id": ba_combo.currentData()
        }))
        form.addRow("", btn_save)
        dialog.exec()

    def save_quota(self, dialog, data):
        session = get_db_session()
        try:
            q_id = data.pop('id')
            exists_q = session.query(LeaveQuota).filter_by(
                year=data['year'], leave_type=data['leave_type'],
                company_id=data['company_id'], business_area_id=data['business_area_id']
            )
            if q_id:
                exists_q = exists_q.filter(LeaveQuota.id != q_id)
            if exists_q.first():
                QMessageBox.warning(dialog, "Duplicate", "Quota already exists for this combination.")
                return
            if q_id:
                q = session.get(LeaveQuota, q_id)
                for k, v in data.items():
                    setattr(q, k, v)
            else:
                session.add(LeaveQuota(**data))
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
