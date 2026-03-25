from ui.custom_widgets import make_input_group
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QFormLayout, QMessageBox, QHeaderView, QComboBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import get_db_session
from models import BusinessArea, Company, Shift


class BusinessAreaManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    # ─────────────────────────────────────────────────────────────────────
    # UI Setup
    # ─────────────────────────────────────────────────────────────────────
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────────
        header = QHBoxLayout()

        title = QLabel("Business Area Manager")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a237e;")
        header.addWidget(title)

        header.addStretch()

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setStyleSheet(self._btn_style("#607d8b"))
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)

        btn_add = QPushButton("➕  Add Business Area")
        btn_add.setStyleSheet(self._btn_style("#2196F3"))
        btn_add.clicked.connect(lambda: self._open_dialog(None))
        header.addWidget(btn_add)

        root.addLayout(header)

        # ── Filter bar ──────────────────────────────────────────────────
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        filter_bar.addWidget(QLabel("Filter by Company:"))
        self.cmb_company_filter = QComboBox()
        self.cmb_company_filter.setMinimumWidth(200)
        self.cmb_company_filter.currentIndexChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.cmb_company_filter)
        filter_bar.addStretch()

        root.addLayout(filter_bar)

        # ── Table ────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Company", "Shifts", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().hide()




        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 6px; gridline-color: #eee; }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:alternate { background: #f9f9f9; }
        """)
        root.addWidget(self.table)

        # ── Summary label ────────────────────────────────────────────────
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color: #666; font-size: 12px;")
        root.addWidget(self.lbl_count)

    # ─────────────────────────────────────────────────────────────────────
    # Data Loading
    # ─────────────────────────────────────────────────────────────────────
    def load_data(self):
        session = get_db_session()
        self._all_areas = session.query(BusinessArea).join(Company).order_by(
            Company.name, BusinessArea.code
        ).all()
        companies = session.query(Company).order_by(Company.name).all()

        # Rebuild company filter combo
        self.cmb_company_filter.blockSignals(True)
        current_company_id = self.cmb_company_filter.currentData()
        self.cmb_company_filter.clear()
        self.cmb_company_filter.addItem("All Companies", None)
        for c in companies:
            self.cmb_company_filter.addItem(c.name, c.id)
        # Restore selection if possible
        for i in range(self.cmb_company_filter.count()):
            if self.cmb_company_filter.itemData(i) == current_company_id:
                self.cmb_company_filter.setCurrentIndex(i)
                break
        self.cmb_company_filter.blockSignals(False)

        self._apply_filter()

    def _apply_filter(self):
        company_id = self.cmb_company_filter.currentData()
        if company_id is None:
            areas = self._all_areas
        else:
            areas = [a for a in self._all_areas if a.company_id == company_id]

        self._populate_table(areas)
        total = len(self._all_areas)
        shown = len(areas)
        self.lbl_count.setText(f"Showing {shown} of {total} business area(s)")

    def _populate_table(self, areas):
        self.table.setRowCount(0)
        for row, ba in enumerate(areas):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(ba.id)))
            self.table.setItem(row, 1, QTableWidgetItem(ba.code))
            self.table.setItem(row, 2, QTableWidgetItem(ba.name))
            company_name = ba.company.name if ba.company else "—"
            self.table.setItem(row, 3, QTableWidgetItem(company_name))

            # Shift count scoped to this BA
            session_inner = get_db_session()
            shift_count = session_inner.query(Shift).filter_by(business_area_id=ba.id).count()
            shift_item = QTableWidgetItem(str(shift_count) if shift_count else "—")
            shift_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, shift_item)

            # Action buttons
            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4, 2, 4, 2)
            action_l.setSpacing(6)

            btn_edit = QPushButton("✏ Edit")
            btn_edit.setStyleSheet(self._btn_style("#FF9800", small=True))
            btn_edit.clicked.connect(lambda _, x=ba: self._open_dialog(x))

            btn_del = QPushButton("🗑 Delete")
            btn_del.setStyleSheet(self._btn_style("#f44336", small=True))
            btn_del.clicked.connect(lambda _, x=ba: self._delete(x))

            action_l.addWidget(btn_edit)
            action_l.addWidget(btn_del)
            self.table.setCellWidget(row, 5, action_w)

    # ─────────────────────────────────────────────────────────────────────
    # Add / Edit Dialog
    # ─────────────────────────────────────────────────────────────────────
    def _open_dialog(self, ba_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Business Area" if ba_obj else "Add Business Area")
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet("background: #fff;")

        form = QFormLayout(dialog)
        form.setSpacing(10)
        form.setContentsMargins(20, 20, 20, 20)

        # Company combo
        session = get_db_session()
        companies = session.query(Company).order_by(Company.name).all()

        cmb_company = QComboBox()
        for c in companies:
            cmb_company.addItem(f"{c.code} — {c.name}", c.id)
        if ba_obj:
            for i in range(cmb_company.count()):
                if cmb_company.itemData(i) == ba_obj.company_id:
                    cmb_company.setCurrentIndex(i)
                    break
        form.addRow(make_input_group("Company:", cmb_company))

        # Code
        txt_code = QLineEdit()
        txt_code.setMaxLength(2)
        txt_code.setPlaceholderText("2-digit code, e.g. 01")
        if ba_obj:
            txt_code.setText(ba_obj.code)
        form.addRow(make_input_group("Area Code (2 digits):", txt_code))

        # Name
        txt_name = QLineEdit()
        txt_name.setPlaceholderText("e.g. Head Office, Factory, Warehouse")
        if ba_obj:
            txt_name.setText(ba_obj.name)
        form.addRow(make_input_group("Area Name:", txt_name))

        # Button row
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(self._btn_style("#4CAF50"))
        btn_save.setDefault(True)
        btn_save.clicked.connect(
            lambda: self._save(dialog, ba_obj, cmb_company.currentData(),
                               txt_code.text().strip(), txt_name.text().strip())
        )
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        form.addRow(btn_row)

        if not companies:
            QMessageBox.warning(self, "No Companies",
                                "Please add at least one company before creating business areas.")
            return

        dialog.exec()

    # ─────────────────────────────────────────────────────────────────────
    # CRUD Operations
    # ─────────────────────────────────────────────────────────────────────
    def _save(self, dialog, ba_obj, company_id, code, name):
        if len(code) != 2:
            QMessageBox.warning(dialog, "Validation Error", "Area Code must be exactly 2 characters.")
            return
        if not name:
            QMessageBox.warning(dialog, "Validation Error", "Area Name is required.")
            return
        if not company_id:
            QMessageBox.warning(dialog, "Validation Error", "Please select a company.")
            return

        session = get_db_session()
        try:
            # Uniqueness check within company
            dup_q = session.query(BusinessArea).filter_by(company_id=company_id, code=code)
            if ba_obj:
                dup_q = dup_q.filter(BusinessArea.id != ba_obj.id)
            if dup_q.first():
                QMessageBox.warning(dialog, "Duplicate Code",
                                    f"Area code '{code}' already exists in this company.")
                return

            if ba_obj:
                ba = session.get(BusinessArea, ba_obj.id)
                ba.code = code
                ba.name = name
                ba.company_id = company_id
            else:
                ba = BusinessArea(code=code, name=name, company_id=company_id)
                session.add(ba)

            session.commit()
            dialog.accept()
            self.load_data()

        except Exception as e:
            session.rollback()
            QMessageBox.critical(dialog, "Database Error", str(e))

    def _delete(self, ba):
        # Count employees in this area
        session = get_db_session()
        from models import Employee
        emp_count = session.query(Employee).filter_by(business_area_id=ba.id).count()

        msg = f"Delete business area '{ba.name}' (code: {ba.code})?"
        if emp_count > 0:
            msg += f"\n\n⚠ {emp_count} employee(s) belong to this area. Their business area will be set to None."

        confirm = QMessageBox.question(
            self, "Confirm Delete", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            # Nullify employee references first
            if emp_count > 0:
                from models import Employee
                session.query(Employee).filter_by(business_area_id=ba.id).update(
                    {"business_area_id": None}
                )
            session.query(BusinessArea).filter_by(id=ba.id).delete()
            session.commit()
            self.load_data()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────
    # Style helpers
    # ─────────────────────────────────────────────────────────────────────
    @staticmethod
    def _btn_style(color: str, small: bool = False) -> str:
        pad = "4px 10px" if small else "6px 16px"
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: {pad};
                font-weight: bold;
                font-size: {"11px" if small else "12px"};
            }}
            QPushButton:hover {{ opacity: 0.85; background-color: {color}cc; }}
            QPushButton:pressed {{ background-color: {color}99; }}
        """
