from ui.btn_styles import btn_primary, btn_neutral, btn_small_edit, btn_small_delete
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QFormLayout, QMessageBox, QTimeEdit, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, QTime
from database import get_db_session
from models import Shift, Company, BusinessArea
from services.shift_service import ShiftService
from config import Config


class ShiftManagement(QWidget):
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

        btn_add = QPushButton("＋  Add Shift")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_shift_dialog(None))

        layout.addWidget(make_page_header("Shift Manager",
                                          "Define work shifts for companies and business areas",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        # Filter bar
        filter_row = QHBoxLayout()
        lbl = QLabel("Filter by Company:")
        lbl.setStyleSheet("background: transparent;")
        self.cmb_filter = QComboBox()
        self.cmb_filter.setMinimumWidth(200)
        self.cmb_filter.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(lbl)
        filter_row.addWidget(self.cmb_filter)
        filter_row.addStretch()
        cl.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Name", "Company", "Business Area", "Start", "End", "Late (min)", "Actions"])
        apply_table_defaults(self.table,
                             stretch_cols=[0, 1, 2],
                             fixed_cols={3: 80, 4: 80, 5: 80, 6: 160})
        cl.addWidget(self.table)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color: #55557a; font-size: 12px; background: transparent;")
        cl.addWidget(self.lbl_count)

        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        self._all_shifts = session.query(Shift).join(
            Company, Shift.company_id == Company.id, isouter=True
        ).order_by(Company.name, Shift.name).all()

        companies = session.query(Company).order_by(Company.name).all()
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
        shifts = self._all_shifts if cid is None else [
            s for s in self._all_shifts if s.company_id == cid or s.company_id is None
        ]
        self._populate_table(shifts)
        self.lbl_count.setText(f"Showing {len(shifts)} of {len(self._all_shifts)} shift(s)")

    def _populate_table(self, shifts):
        fmt = Config.get_time_fmt()
        self.table.setRowCount(0)
        for row, shift in enumerate(shifts):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(shift.name))
            self.table.setItem(row, 1, QTableWidgetItem(shift.company.name if shift.company else "Global"))
            self.table.setItem(row, 2, QTableWidgetItem(shift.business_area.name if shift.business_area else "All Areas"))
            self.table.setItem(row, 3, QTableWidgetItem(shift.start_time.strftime(fmt)))
            self.table.setItem(row, 4, QTableWidgetItem(shift.end_time.strftime(fmt)))
            self.table.setItem(row, 5, QTableWidgetItem(str(shift.late_allowance_minutes)))

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            b1 = QPushButton("Edit")
            b1.setStyleSheet(btn_small_edit())
            b1.clicked.connect(lambda _, x=shift: self.add_shift_dialog(x))
            al.addWidget(b1)
            b2 = QPushButton("Delete")
            b2.setStyleSheet(btn_small_delete())
            b2.clicked.connect(lambda _, x=shift: self.delete_shift(x))
            al.addWidget(b2)
            self.table.setCellWidget(row, 6, aw)

    def add_shift_dialog(self, shift_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Shift" if shift_obj else "Add Shift")
        style_dialog(dialog, min_width=420)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        session = get_db_session()
        companies = session.query(Company).order_by(Company.name).all()

        name_input = QLineEdit(shift_obj.name if shift_obj else "")
        name_input.setPlaceholderText("Shift name")

        cmb_company = QComboBox()
        cmb_company.addItem("Global (All Companies)", None)
        for c in companies:
            cmb_company.addItem(c.name, c.id)
        if shift_obj and shift_obj.company_id:
            for i in range(cmb_company.count()):
                if cmb_company.itemData(i) == shift_obj.company_id:
                    cmb_company.setCurrentIndex(i)
                    break

        cmb_ba = QComboBox()

        def refresh_ba():
            cmb_ba.clear()
            cmb_ba.addItem("All Business Areas", None)
            cid = cmb_company.currentData()
            if cid:
                for ba in session.query(BusinessArea).filter_by(company_id=cid).order_by(BusinessArea.name).all():
                    cmb_ba.addItem(ba.name, ba.id)
            cmb_ba.setEnabled(bool(cid))

        cmb_company.currentIndexChanged.connect(refresh_ba)
        refresh_ba()
        if shift_obj and shift_obj.business_area_id:
            for i in range(cmb_ba.count()):
                if cmb_ba.itemData(i) == shift_obj.business_area_id:
                    cmb_ba.setCurrentIndex(i)
                    break

        time_fmt = Config.get_qt_time_fmt()
        start_input = QTimeEdit()
        start_input.setDisplayFormat(time_fmt)
        start_input.setTime(QTime(shift_obj.start_time.hour, shift_obj.start_time.minute) if shift_obj else QTime(9, 0))

        end_input = QTimeEdit()
        end_input.setDisplayFormat(time_fmt)
        end_input.setTime(QTime(shift_obj.end_time.hour, shift_obj.end_time.minute) if shift_obj else QTime(17, 0))

        allowance_input = QSpinBox()
        allowance_input.setRange(0, 120)
        allowance_input.setSuffix(" min")
        allowance_input.setValue(shift_obj.late_allowance_minutes if shift_obj else 15)

        form.addRow("Shift Name:", name_input)
        form.addRow("Company Scope:", cmb_company)
        form.addRow("Business Area:", cmb_ba)
        form.addRow("Start Time:", start_input)
        form.addRow("End Time:", end_input)
        form.addRow("Late Allowance:", allowance_input)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(btn_neutral())
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Save Shift")
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
                ShiftService.create_shift(session, name, start, end, allowance,
                                          company_id=company_id, business_area_id=ba_id)
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
        if QMessageBox.question(self, "Confirm Delete", msg,
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) != QMessageBox.StandardButton.Yes:
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
