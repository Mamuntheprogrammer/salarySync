from ui.btn_styles import btn_small_delete, btn_primary, btn_small_edit, btn_neutral
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QDialog,
                             QFormLayout, QMessageBox, QComboBox,
                             QLineEdit, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate
from database import get_db_session
from models import Bonus, Employee
from ui.page_helpers import make_page_header, apply_table_defaults, style_dialog


class BonusManagement(QWidget):
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

        btn_add = QPushButton("＋  Add Bonus")
        btn_add.setStyleSheet(btn_primary())
        btn_add.clicked.connect(lambda: self.add_dialog(None))

        layout.addWidget(make_page_header("Bonus Manager",
                                          "Configure and manage employee bonuses",
                                          extra_widgets=[btn_refresh, btn_add]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Employee", "Period", "Type", "Amount", "Description", "Actions"])
        apply_table_defaults(self.table,
                             stretch_cols=[0, 4],
                             fixed_cols={1: 80, 2: 110, 3: 90, 5: 140})
        cl.addWidget(self.table)
        layout.addWidget(content, stretch=1)

    def load_data(self):
        session = get_db_session()
        bonuses = session.query(Bonus).order_by(Bonus.year.desc(), Bonus.month.desc()).all()
        self.table.setRowCount(0)
        for row, b in enumerate(bonuses):
            self.table.insertRow(row)
            emp_name = f"{b.employee.id} — {b.employee.full_name}" if b.employee else "Unknown"
            self.table.setItem(row, 0, QTableWidgetItem(emp_name))
            self.table.setItem(row, 1, QTableWidgetItem(f"{b.year}-{b.month:02d}"))
            self.table.setItem(row, 2, QTableWidgetItem("Percentage" if b.is_percentage else "Fixed"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{b.amount}%" if b.is_percentage else f"{b.amount:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(b.description or ""))

            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(btn_small_edit())
            btn_edit.clicked.connect(lambda _, x=b: self.add_dialog(x))
            al.addWidget(btn_edit)
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet(btn_small_delete())
            btn_del.clicked.connect(lambda _, x=b: self.delete_bonus(x))
            al.addWidget(btn_del)
            self.table.setCellWidget(row, 5, aw)

    def delete_bonus(self, bonus):
        if QMessageBox.question(self, "Confirm", "Delete this bonus record?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Bonus).filter(Bonus.id == bonus.id).delete()
            session.commit()
            self.load_data()

    def add_dialog(self, bonus_obj=None):
        session = get_db_session()
        employees = session.query(Employee).filter_by(is_active=True).all()

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Bonus" if bonus_obj else "Add Bonus")
        style_dialog(dialog, min_width=440)

        form = QFormLayout(dialog)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        emp_combo = QComboBox()
        for e in employees:
            emp_combo.addItem(f"{e.id} — {e.full_name}", e.id)
        if bonus_obj and bonus_obj.employee_id:
            idx = emp_combo.findData(bonus_obj.employee_id)
            if idx >= 0:
                emp_combo.setCurrentIndex(idx)

        current_date = QDate.currentDate()
        month_spin = QSpinBox()
        month_spin.setRange(1, 12)
        month_spin.setValue(bonus_obj.month if bonus_obj else current_date.month())

        year_spin = QSpinBox()
        year_spin.setRange(2000, 2100)
        year_spin.setValue(bonus_obj.year if bonus_obj else current_date.year())

        type_combo = QComboBox()
        type_combo.addItems(["Fixed Amount", "Percentage"])
        if bonus_obj and bonus_obj.is_percentage:
            type_combo.setCurrentText("Percentage")

        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0.0, 1_000_000.0)
        amount_spin.setDecimals(2)
        if bonus_obj:
            amount_spin.setValue(bonus_obj.amount)

        desc_input = QLineEdit()
        desc_input.setPlaceholderText("Optional description")
        if bonus_obj:
            desc_input.setText(bonus_obj.description or "")

        form.addRow("Employee:", emp_combo)
        form.addRow("Month:", month_spin)
        form.addRow("Year:", year_spin)
        form.addRow("Type:", type_combo)
        form.addRow("Amount:", amount_spin)
        form.addRow("Description:", desc_input)

        btn_save = QPushButton("Save Bonus")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_bonus(dialog, bonus_obj, {
            "employee_id": emp_combo.currentData(),
            "month": month_spin.value(),
            "year": year_spin.value(),
            "amount": amount_spin.value(),
            "is_percentage": type_combo.currentText() == "Percentage",
            "description": desc_input.text()
        }))
        form.addRow("", btn_save)
        dialog.exec()

    def save_bonus(self, dialog, bonus_obj, data):
        session = get_db_session()
        try:
            if data['amount'] < 0:
                raise ValueError("Amount cannot be negative.")
            if bonus_obj:
                b = session.get(Bonus, bonus_obj.id)
                for k, v in data.items():
                    setattr(b, k, v)
            else:
                session.add(Bonus(**data))
            session.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))
