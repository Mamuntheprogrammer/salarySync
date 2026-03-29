from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QDialog,
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Company, BusinessArea
from ui.btn_styles import btn_small_edit, btn_small_delete, btn_primary, btn_neutral
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog


class CompanyManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        btn_refresh = QPushButton("⟳  Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)

        btn_add = QPushButton("＋  Add Company")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_company_dialog(None))

        layout.addWidget(make_page_header("Company Management",
                                          "Manage companies and their business areas",
                                          extra_widgets=[btn_refresh, btn_add]))

        # Table
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Business Areas", "Actions"])
        apply_table_defaults(self.table,
                             stretch_cols=[0, 1, 2, 3],
                             fixed_cols={4: 200})
        content_layout.addWidget(self.table)
        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        companies = session.query(Company).all()
        self.table.setRowCount(0)
        for row, comp in enumerate(companies):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(comp.id)))
            self.table.setItem(row, 1, QTableWidgetItem(comp.code))
            self.table.setItem(row, 2, QTableWidgetItem(comp.name))

            ba_names = ", ".join([ba.name for ba in comp.business_areas])
            self.table.setItem(row, 3, QTableWidgetItem(ba_names))

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)

            btn_manage = QPushButton("Areas")
            btn_manage.setStyleSheet(btn_small_edit())
            btn_manage.clicked.connect(lambda _, c=comp: self.manage_areas_dialog(c))
            al.addWidget(btn_manage)

            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(btn_small_edit())
            btn_edit.clicked.connect(lambda _, x=comp: self.add_company_dialog(x))
            al.addWidget(btn_edit)

            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet(btn_small_delete())
            btn_del.clicked.connect(lambda _, x=comp: self.delete_company(x))
            al.addWidget(btn_del)

            self.table.setCellWidget(row, 4, aw)

    def delete_company(self, company):
        confirm = QMessageBox.question(self, "Confirm Delete",
                                       f"Delete company '{company.name}'?\nThis will remove all associated business areas.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Company).filter_by(id=company.id).delete()
            session.commit()
            self.load_data()

    def add_company_dialog(self, company_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Company" if company_obj else "Add Company")
        style_dialog(dialog, min_width=400)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        code_input = QLineEdit()
        code_input.setMaxLength(4)
        code_input.setPlaceholderText("3 or 4 character code")
        if company_obj:
            code_input.setText(company_obj.code)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Full company name")
        if company_obj:
            name_input.setText(company_obj.name)

        form.addRow("Company Code:", code_input)
        form.addRow("Company Name:", name_input)

        btn_save = QPushButton("Save Company")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_company(dialog, company_obj,
                                                            code_input.text(),
                                                            name_input.text()))
        form.addRow("", btn_save)
        dialog.exec()

    def save_company(self, dialog, company_obj, code, name):
        if len(code) < 3 or len(code) > 4:
            QMessageBox.warning(dialog, "Validation", "Code must be 3 or 4 characters")
            return
        if not name:
            QMessageBox.warning(dialog, "Validation", "Name is required")
            return

        session = get_db_session()
        try:
            exists_q = session.query(Company).filter_by(code=code)
            if company_obj:
                exists_q = exists_q.filter(Company.id != company_obj.id)
            if exists_q.first():
                QMessageBox.warning(dialog, "Duplicate", "Company code already exists")
                return
            if company_obj:
                c = session.get(Company, company_obj.id)
                c.code = code
                c.name = name
            else:
                session.add(Company(code=code, name=name))
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))

    def manage_areas_dialog(self, company):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Business Areas — {company.name}")
        style_dialog(dialog, min_width=560, min_height=420)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Add area row
        add_row = QHBoxLayout()
        code_input = QLineEdit()
        code_input.setMaxLength(2)
        code_input.setPlaceholderText("Code (2 digits)")
        code_input.setFixedWidth(110)
        name_input = QLineEdit()
        name_input.setPlaceholderText("Area name")

        btn_add = QPushButton("Add Area")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self._save_ba(dialog, None, company.id,
                                                       code_input.text(), name_input.text()))
        add_row.addWidget(code_input)
        add_row.addWidget(name_input)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        self.ba_table = QTableWidget()
        self.ba_table.setColumnCount(3)
        self.ba_table.setHorizontalHeaderLabels(["Code", "Name", "Actions"])
        apply_table_defaults(self.ba_table,
                             stretch_cols=[0, 1],
                             fixed_cols={2: 160})
        layout.addWidget(self.ba_table)

        self._load_ba_table(company.id)
        dialog.exec()
        self.load_data()

    def _load_ba_table(self, company_id):
        session = get_db_session()
        areas = session.query(BusinessArea).filter_by(company_id=company_id).all()
        self.ba_table.setRowCount(0)
        for row, ba in enumerate(areas):
            self.ba_table.insertRow(row)
            self.ba_table.setItem(row, 0, QTableWidgetItem(ba.code))
            self.ba_table.setItem(row, 1, QTableWidgetItem(ba.name))

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)

            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(btn_small_edit())
            btn_edit.clicked.connect(lambda _, x=ba: self._edit_ba_dialog(x, company_id))
            al.addWidget(btn_edit)

            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet(btn_small_delete())
            btn_del.clicked.connect(lambda _, x=ba: self._delete_ba(x, company_id))
            al.addWidget(btn_del)
            self.ba_table.setCellWidget(row, 2, aw)

    def _delete_ba(self, ba, company_id):
        confirm = QMessageBox.question(None, "Confirm",
                                       f"Delete business area '{ba.name}'?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(BusinessArea).filter_by(id=ba.id).delete()
            session.commit()
            self._load_ba_table(company_id)

    def _edit_ba_dialog(self, ba, company_id):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Business Area")
        style_dialog(dialog, min_width=360)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        code_input = QLineEdit(ba.code)
        code_input.setMaxLength(2)
        name_input = QLineEdit(ba.name)

        form.addRow("Code:", code_input)
        form.addRow("Name:", name_input)

        btn_save = QPushButton("Save Changes")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self._save_ba(dialog, ba, company_id,
                                                        code_input.text(), name_input.text()))
        form.addRow("", btn_save)
        dialog.exec()
        self._load_ba_table(company_id)

    def _save_ba(self, dialog, ba_obj, company_id, code, name):
        if len(code) != 2 or not code.isdigit():
            QMessageBox.warning(dialog, "Validation", "Code must be exactly 2 digits")
            return
        if not name:
            QMessageBox.warning(dialog, "Validation", "Name is required")
            return

        session = get_db_session()
        existing = session.query(BusinessArea).filter_by(company_id=company_id, code=code)
        if ba_obj:
            existing = existing.filter(BusinessArea.id != ba_obj.id)
        if existing.first():
            QMessageBox.warning(dialog, "Duplicate", "Code already exists in this company")
            return

        try:
            if ba_obj:
                ba = session.get(BusinessArea, ba_obj.id)
                ba.code = code
                ba.name = name
                if dialog.windowTitle() == "Edit Business Area":
                    dialog.accept()
            else:
                session.add(BusinessArea(code=code, name=name, company_id=company_id))
                self._load_ba_table(company_id)
            session.commit()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
