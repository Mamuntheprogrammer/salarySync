from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QDialog,
                             QLineEdit, QFormLayout, QMessageBox, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Designation, DesignationSubcategory
from ui.btn_styles import btn_primary, btn_neutral, btn_small_edit, btn_small_delete
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog


class DesignationManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_designations()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        btn_refresh = QPushButton("⟳  Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_designations)

        btn_add = QPushButton("＋  Add Designation")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_designation_dialog(None))

        layout.addWidget(make_page_header("Designation & Levels",
                                          "Manage designations and sub-level categories",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # Left: Designations
        left_group = QGroupBox("Designations")
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(8, 10, 8, 8)

        self.table_deg = QTableWidget()
        self.table_deg.setColumnCount(3)
        self.table_deg.setHorizontalHeaderLabels(["ID", "Name", "Actions"])
        apply_table_defaults(self.table_deg, stretch_cols=[0, 1], fixed_cols={2: 140})
        self.table_deg.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_deg.itemSelectionChanged.connect(self.on_designation_selected)
        left_layout.addWidget(self.table_deg)
        splitter.addWidget(left_group)

        # Right: Subcategories
        self.right_group = QGroupBox("Subcategories")
        right_layout = QVBoxLayout(self.right_group)
        right_layout.setContentsMargins(8, 10, 8, 8)

        sub_header = QHBoxLayout()
        sub_header.addStretch()
        self.btn_add_s = QPushButton("＋  Add Subcategory")
        self.btn_add_s.setStyleSheet(btn_primary())
        self.btn_add_s.setEnabled(False)
        self.btn_add_s.clicked.connect(lambda: self.add_subcategory_dialog(None))
        sub_header.addWidget(self.btn_add_s)
        right_layout.addLayout(sub_header)

        self.table_sub = QTableWidget()
        self.table_sub.setColumnCount(3)
        self.table_sub.setHorizontalHeaderLabels(["ID", "Name", "Actions"])
        apply_table_defaults(self.table_sub, stretch_cols=[0, 1], fixed_cols={2: 140})
        right_layout.addWidget(self.table_sub)
        splitter.addWidget(self.right_group)
        splitter.setSizes([350, 450])

        cl.addWidget(splitter)
        layout.addWidget(content, stretch=1)

    def load_designations(self):
        session = get_db_session()
        self.table_deg.setRowCount(0)
        self.table_sub.setRowCount(0)
        self.right_group.setTitle("Subcategories")
        self.btn_add_s.setEnabled(False)

        for row, deg in enumerate(session.query(Designation).all()):
            self.table_deg.insertRow(row)
            self.table_deg.setItem(row, 0, QTableWidgetItem(str(deg.id)))
            self.table_deg.setItem(row, 1, QTableWidgetItem(deg.name))
            self.table_deg.setCellWidget(row, 2, self._action_widget(
                lambda _, x=deg: self.add_designation_dialog(x),
                lambda _, x=deg: self.delete_designation(x)
            ))

    def load_data(self):
        self.load_designations()

    def _action_widget(self, edit_fn, delete_fn):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(4)
        b1 = QPushButton("Edit")
        b1.setStyleSheet(btn_small_edit())
        b1.clicked.connect(edit_fn)
        b2 = QPushButton("Delete")
        b2.setStyleSheet(btn_small_delete())
        b2.clicked.connect(delete_fn)
        h.addWidget(b1)
        h.addWidget(b2)
        return w

    def delete_designation(self, deg):
        if QMessageBox.question(self, "Confirm Delete",
                                f"Delete '{deg.name}' and all its subcategories?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Designation).filter_by(id=deg.id).delete()
            session.commit()
            self.load_designations()

    def on_designation_selected(self):
        items = self.table_deg.selectedItems()
        if not items:
            return
        row = items[0].row()
        deg_id = int(self.table_deg.item(row, 0).text())
        deg_name = self.table_deg.item(row, 1).text()
        self.right_group.setTitle(f"{deg_name}  —  Subcategories")
        self.btn_add_s.setEnabled(True)
        self.load_subcategories(deg_id)

    def load_subcategories(self, deg_id):
        session = get_db_session()
        self.table_sub.setRowCount(0)
        for row, sub in enumerate(session.query(DesignationSubcategory).filter_by(designation_id=deg_id).all()):
            self.table_sub.insertRow(row)
            self.table_sub.setItem(row, 0, QTableWidgetItem(str(sub.id)))
            self.table_sub.setItem(row, 1, QTableWidgetItem(sub.name))
            self.table_sub.setCellWidget(row, 2, self._action_widget(
                lambda _, x=sub: self.add_subcategory_dialog(x),
                lambda _, x=sub: self.delete_subcategory(x)
            ))

    def delete_subcategory(self, sub):
        if QMessageBox.question(self, "Confirm", f"Delete subcategory '{sub.name}'?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            deg_id = sub.designation_id
            session.query(DesignationSubcategory).filter_by(id=sub.id).delete()
            session.commit()
            self.load_subcategories(deg_id)

    def _simple_name_dialog(self, title, current_name=""):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        style_dialog(dialog, min_width=360)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        name_input = QLineEdit(current_name)
        name_input.setPlaceholderText("Enter name")
        form.addRow("Name:", name_input)

        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(btn_primary())
        form.addRow("", btn_save)
        return dialog, name_input, btn_save

    def add_designation_dialog(self, deg_obj=None):
        dialog, name_input, btn_save = self._simple_name_dialog(
            "Edit Designation" if deg_obj else "Add Designation",
            deg_obj.name if deg_obj else ""
        )
        btn_save.clicked.connect(lambda: self._save_designation(dialog, deg_obj, name_input.text()))
        dialog.exec()

    def _save_designation(self, dialog, deg_obj, name):
        if not name.strip():
            QMessageBox.warning(dialog, "Validation", "Name is required")
            return
        session = get_db_session()
        try:
            if deg_obj:
                d = session.get(Designation, deg_obj.id)
                d.name = name.strip()
            else:
                session.add(Designation(name=name.strip()))
            session.commit()
            dialog.accept()
            self.load_designations()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))

    def add_subcategory_dialog(self, sub_obj=None):
        deg_id = None
        if not sub_obj:
            items = self.table_deg.selectedItems()
            if not items:
                return
            deg_id = int(self.table_deg.item(items[0].row(), 0).text())
        else:
            deg_id = sub_obj.designation_id

        dialog, name_input, btn_save = self._simple_name_dialog(
            "Edit Subcategory" if sub_obj else "Add Subcategory",
            sub_obj.name if sub_obj else ""
        )
        btn_save.clicked.connect(lambda: self._save_subcategory(dialog, sub_obj, deg_id, name_input.text()))
        dialog.exec()

    def _save_subcategory(self, dialog, sub_obj, deg_id, name):
        if not name.strip():
            QMessageBox.warning(dialog, "Validation", "Name is required")
            return
        session = get_db_session()
        try:
            if sub_obj:
                s = session.get(DesignationSubcategory, sub_obj.id)
                s.name = name.strip()
            else:
                session.add(DesignationSubcategory(name=name.strip(), designation_id=deg_id))
            session.commit()
            dialog.accept()
            self.load_subcategories(deg_id)
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
