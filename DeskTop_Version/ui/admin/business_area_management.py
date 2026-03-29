from ui.btn_styles import btn_primary, btn_neutral, btn_small_edit, btn_small_delete
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QFormLayout, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import BusinessArea, Company, Shift, Employee


class BusinessAreaManagement(QWidget):
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

        btn_add = QPushButton("＋  Add Business Area")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self._open_dialog(None))

        layout.addWidget(make_page_header("Business Area Manager",
                                          "Manage business areas / branches within companies",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        # Filter bar
        filter_row = QHBoxLayout()
        lbl = QLabel("Filter by Company:")
        lbl.setStyleSheet("background: transparent;")
        self.cmb_company_filter = QComboBox()
        self.cmb_company_filter.setMinimumWidth(200)
        self.cmb_company_filter.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(lbl)
        filter_row.addWidget(self.cmb_company_filter)
        filter_row.addStretch()
        cl.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Company", "Shifts", "Actions"])
        apply_table_defaults(self.table,
                             stretch_cols=[2, 3],
                             fixed_cols={0: 50, 1: 60, 4: 55, 5: 140})
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        cl.addWidget(self.table)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color: #55557a; font-size: 12px; background: transparent;")
        cl.addWidget(self.lbl_count)

        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        self._all_areas = session.query(BusinessArea).join(Company).order_by(
            Company.name, BusinessArea.code
        ).all()
        companies = session.query(Company).order_by(Company.name).all()

        self.cmb_company_filter.blockSignals(True)
        current = self.cmb_company_filter.currentData()
        self.cmb_company_filter.clear()
        self.cmb_company_filter.addItem("All Companies", None)
        for c in companies:
            self.cmb_company_filter.addItem(c.name, c.id)
        for i in range(self.cmb_company_filter.count()):
            if self.cmb_company_filter.itemData(i) == current:
                self.cmb_company_filter.setCurrentIndex(i)
                break
        self.cmb_company_filter.blockSignals(False)
        self._apply_filter()

    def _apply_filter(self):
        company_id = self.cmb_company_filter.currentData()
        areas = self._all_areas if company_id is None else [
            a for a in self._all_areas if a.company_id == company_id
        ]
        self._populate_table(areas)
        self.lbl_count.setText(f"Showing {len(areas)} of {len(self._all_areas)} business area(s)")

    def _populate_table(self, areas):
        session = get_db_session()
        self.table.setRowCount(0)
        for row, ba in enumerate(areas):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(ba.id)))
            self.table.setItem(row, 1, QTableWidgetItem(ba.code))
            self.table.setItem(row, 2, QTableWidgetItem(ba.name))
            self.table.setItem(row, 3, QTableWidgetItem(ba.company.name if ba.company else "—"))

            shift_count = session.query(Shift).filter_by(business_area_id=ba.id).count()
            sc_item = QTableWidgetItem(str(shift_count) if shift_count else "—")
            sc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, sc_item)

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            b1 = QPushButton("Edit")
            b1.setStyleSheet(btn_small_edit())
            b1.clicked.connect(lambda _, x=ba: self._open_dialog(x))
            al.addWidget(b1)
            b2 = QPushButton("Delete")
            b2.setStyleSheet(btn_small_delete())
            b2.clicked.connect(lambda _, x=ba: self._delete(x))
            al.addWidget(b2)
            self.table.setCellWidget(row, 5, aw)

    def _open_dialog(self, ba_obj=None):
        session = get_db_session()
        companies = session.query(Company).order_by(Company.name).all()
        if not companies:
            QMessageBox.warning(self, "No Companies",
                                "Please add at least one company before creating business areas.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Business Area" if ba_obj else "Add Business Area")
        style_dialog(dialog, min_width=400)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        cmb_company = QComboBox()
        for c in companies:
            cmb_company.addItem(f"{c.code} — {c.name}", c.id)
        if ba_obj:
            for i in range(cmb_company.count()):
                if cmb_company.itemData(i) == ba_obj.company_id:
                    cmb_company.setCurrentIndex(i)
                    break

        txt_code = QLineEdit()
        txt_code.setMaxLength(2)
        txt_code.setPlaceholderText("2-digit code  e.g. 01")
        if ba_obj:
            txt_code.setText(ba_obj.code)

        txt_name = QLineEdit()
        txt_name.setPlaceholderText("e.g. Head Office, Factory, Warehouse")
        if ba_obj:
            txt_name.setText(ba_obj.name)

        form.addRow("Company:", cmb_company)
        form.addRow("Area Code (2 digits):", txt_code)
        form.addRow("Area Name:", txt_name)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(btn_neutral())
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self._save(dialog, ba_obj,
                                                     cmb_company.currentData(),
                                                     txt_code.text().strip(),
                                                     txt_name.text().strip()))
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        form.addRow(btn_row)

        dialog.exec()

    def _save(self, dialog, ba_obj, company_id, code, name):
        if len(code) != 2:
            QMessageBox.warning(dialog, "Validation", "Area Code must be exactly 2 characters.")
            return
        if not name:
            QMessageBox.warning(dialog, "Validation", "Area Name is required.")
            return
        if not company_id:
            QMessageBox.warning(dialog, "Validation", "Please select a company.")
            return
        session = get_db_session()
        try:
            dup_q = session.query(BusinessArea).filter_by(company_id=company_id, code=code)
            if ba_obj:
                dup_q = dup_q.filter(BusinessArea.id != ba_obj.id)
            if dup_q.first():
                QMessageBox.warning(dialog, "Duplicate Code",
                                    f"Area code '{code}' already exists in this company.")
                return
            if ba_obj:
                ba = session.get(BusinessArea, ba_obj.id)
                ba.code, ba.name, ba.company_id = code, name, company_id
            else:
                session.add(BusinessArea(code=code, name=name, company_id=company_id))
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(dialog, "Error", str(e))

    def _delete(self, ba):
        session = get_db_session()
        emp_count = session.query(Employee).filter_by(business_area_id=ba.id).count()
        msg = f"Delete business area '{ba.name}' (code: {ba.code})?"
        if emp_count:
            msg += f"\n\n⚠ {emp_count} employee(s) will have their business area cleared."
        if QMessageBox.question(self, "Confirm Delete", msg,
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) != QMessageBox.StandardButton.Yes:
            return
        try:
            if emp_count:
                session.query(Employee).filter_by(business_area_id=ba.id).update({"business_area_id": None})
            session.query(BusinessArea).filter_by(id=ba.id).delete()
            session.commit()
            self.load_data()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", str(e))
