from ui.custom_widgets import make_input_group
from ui.btn_styles import btn_primary, btn_neutral
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QFormLayout, QMessageBox, QHeaderView, QTimeEdit, QSpinBox, QComboBox
)
from PyQt6.QtCore import QTime
from database import get_db_session
from models import Shift, Company, BusinessArea
from services.shift_service import ShiftService
from config import Config


class ShiftManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    # ─────────────────────────────────────────────────────────
    # UI Setup
    # ─────────────────────────────────────────────────────────
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Shift Management</h2>"))
        header.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)

        btn_add = QPushButton("➕ Add Shift")
        btn_add.setStyleSheet(
            "QPushButton{background:#2196F3;color:white;border:none;border-radius:4px;padding:6px 14px;font-weight:bold;}"
            "QPushButton:hover{background:#1976D2;}"
        )
        btn_add.clicked.connect(lambda: self.add_shift_dialog(None))
        header.addWidget(btn_add)
        layout.addLayout(header)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("Filter by Company:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.setMinimumWidth(200)
        self.cmb_filter.currentIndexChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.cmb_filter)
        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Table — 7 columns
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().hide()

        self.table.setHorizontalHeaderLabels(
            ["Name", "Company", "Business Area", "Start", "End", "Late (min)", "Action"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 160)
        layout.addWidget(self.table)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color:#666;font-size:12px;")
        layout.addWidget(self.lbl_count)

    # ─────────────────────────────────────────────────────────
    # Data loading
    # ─────────────────────────────────────────────────────────
    def load_data(self):
        session = get_db_session()
        self._all_shifts = session.query(Shift).join(
            Company, Shift.company_id == Company.id, isouter=True
        ).order_by(Company.name, Shift.name).all()

        companies = session.query(Company).order_by(Company.name).all()

        # Rebuild filter combo preserving selection
        self.cmb_filter.blockSignals(True)
        prev = self.cmb_filter.currentData()
        self.cmb_filter.clear()
        self.cmb_filter.addItem("All Companies", None)
        for c in companies:
            self.cmb_filter.addItem(c.name, c.id)
        for i in range(self.cmb_filter.count()):
            if self.cmb_filter.itemData(i) == prev:
                self.cmb_filter.setCurrentIndex(i)
                break
        self.cmb_filter.blockSignals(False)

        self._apply_filter()

    def _apply_filter(self):
        cid = self.cmb_filter.currentData()
        if cid is None:
            shifts = self._all_shifts
        else:
            shifts = [s for s in self._all_shifts if s.company_id == cid or s.company_id is None]

        self._populate_table(shifts)
        self.lbl_count.setText(f"Showing {len(shifts)} of {len(self._all_shifts)} shift(s)")

    def _populate_table(self, shifts):
        fmt = Config.get_time_fmt()
        self.table.setRowCount(0)
        for row, shift in enumerate(shifts):
            self.table.insertRow(row)
            company_name = shift.company.name if shift.company else "Global"
            ba_name = shift.business_area.name if shift.business_area else "All Areas"

            self.table.setItem(row, 0, QTableWidgetItem(shift.name))
            self.table.setItem(row, 1, QTableWidgetItem(company_name))
            self.table.setItem(row, 2, QTableWidgetItem(ba_name))
            self.table.setItem(row, 3, QTableWidgetItem(shift.start_time.strftime(fmt)))
            self.table.setItem(row, 4, QTableWidgetItem(shift.end_time.strftime(fmt)))
            self.table.setItem(row, 5, QTableWidgetItem(str(shift.late_allowance_minutes)))

            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(3, 2, 3, 2)
            al.setSpacing(5)

            btn_edit = QPushButton("✏ Edit")
            btn_edit.setStyleSheet(
                "QPushButton{background:#FF9800;color:white;border:none;border-radius:3px;padding:3px 8px;font-size:11px;}"
            )
            btn_edit.clicked.connect(lambda _, x=shift: self.add_shift_dialog(x))

            btn_del = QPushButton("🗑 Delete")
            btn_del.setStyleSheet(
                "QPushButton{background:#f44336;color:white;border:none;border-radius:3px;padding:3px 8px;font-size:11px;}"
            )
            btn_del.clicked.connect(lambda _, x=shift: self.delete_shift(x))

            al.addWidget(btn_edit)
            al.addWidget(btn_del)
            self.table.setCellWidget(row, 6, aw)

    # ─────────────────────────────────────────────────────────
    # Add / Edit dialog
    # ─────────────────────────────────────────────────────────
    def add_shift_dialog(self, shift_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Shift" if shift_obj else "Add Shift")
        dialog.setMinimumWidth(400)
        form = QFormLayout(dialog)
        form.setSpacing(10)
        form.setContentsMargins(18, 18, 18, 18)

        session = get_db_session()
        companies = session.query(Company).order_by(Company.name).all()

        # Name
        name_input = QLineEdit()
        if shift_obj:
            name_input.setText(shift_obj.name)
        form.addRow(make_input_group("Shift Name:", name_input))

        # Company scope
        cmb_company = QComboBox()
        cmb_company.addItem("Global (applies to all)", None)
        for c in companies:
            cmb_company.addItem(c.name, c.id)
        if shift_obj and shift_obj.company_id:
            for i in range(cmb_company.count()):
                if cmb_company.itemData(i) == shift_obj.company_id:
                    cmb_company.setCurrentIndex(i)
                    break
        form.addRow(make_input_group("Company Scope:", cmb_company))

        # Business Area scope
        cmb_ba = QComboBox()
        cmb_ba.addItem("All Business Areas", None)

        def refresh_ba():
            cmb_ba.clear()
            cmb_ba.addItem("All Business Areas", None)
            cid = cmb_company.currentData()
            if cid:
                bas = session.query(BusinessArea).filter_by(company_id=cid).order_by(BusinessArea.name).all()
                for ba in bas:
                    cmb_ba.addItem(ba.name, ba.id)
            cmb_ba.setEnabled(bool(cid))

        cmb_company.currentIndexChanged.connect(refresh_ba)
        refresh_ba()

        if shift_obj and shift_obj.business_area_id:
            for i in range(cmb_ba.count()):
                if cmb_ba.itemData(i) == shift_obj.business_area_id:
                    cmb_ba.setCurrentIndex(i)
                    break
        form.addRow(make_input_group("Business Area Scope:", cmb_ba))

        # Times
        time_fmt = Config.get_qt_time_fmt()
        start_input = QTimeEdit()
        start_input.setDisplayFormat(time_fmt)
        start_input.setTime(
            QTime(shift_obj.start_time.hour, shift_obj.start_time.minute) if shift_obj else QTime(9, 0)
        )
        form.addRow(make_input_group("Start Time:", start_input))

        end_input = QTimeEdit()
        end_input.setDisplayFormat(time_fmt)
        end_input.setTime(
            QTime(shift_obj.end_time.hour, shift_obj.end_time.minute) if shift_obj else QTime(17, 0)
        )
        form.addRow(make_input_group("End Time:", end_input))

        allowance_input = QSpinBox()
        allowance_input.setRange(0, 120)
        allowance_input.setValue(shift_obj.late_allowance_minutes if shift_obj else 15)
        allowance_input.setSuffix(" min")
        form.addRow(make_input_group("Late Allowance:", allowance_input))

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Save")
        btn_save.setDefault(True)
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self._save(
            dialog, shift_obj,
            name_input.text().strip(),
            start_input.time().toPyTime(),
            end_input.time().toPyTime(),
            allowance_input.value(),
            cmb_company.currentData(),
            cmb_ba.currentData(),
        ))
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        form.addRow(btn_row)

        dialog.exec()

    # ─────────────────────────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────────────────────────
    def _save(self, dialog, shift_obj, name, start, end, allowance, company_id, ba_id):
        if not name:
            QMessageBox.warning(dialog, "Validation", "Shift name is required.")
            return
        session = get_db_session()
        try:
            if shift_obj:
                s = session.get(Shift, shift_obj.id)
                s.name = name
                s.start_time = start
                s.end_time = end
                s.late_allowance_minutes = allowance
                s.company_id = company_id
                s.business_area_id = ba_id
                session.commit()
            else:
                ShiftService.create_shift(
                    session, name, start, end, allowance,
                    company_id=company_id, business_area_id=ba_id
                )
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))

    def delete_shift(self, shift):
        session = get_db_session()
        from models import Employee
        emp_count = session.query(Employee).filter_by(shift_id=shift.id).count()
        msg = f"Delete shift '{shift.name}'?"
        if emp_count:
            msg += f"\n\n⚠ {emp_count} employee(s) use this shift. Their shift will be cleared."
        confirm = QMessageBox.question(
            self, "Confirm", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            if emp_count:
                session.query(Employee).filter_by(shift_id=shift.id).update({"shift_id": None})
            session.query(Shift).filter_by(id=shift.id).delete()
            session.commit()
            self.load_data()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", str(e))
