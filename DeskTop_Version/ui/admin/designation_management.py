from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView, QComboBox, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Designation, DesignationSubcategory

class DesignationManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_designations()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # --- Top Header ---
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #333; border-radius: 5px;")
        header_widget.setFixedHeight(60) # Force compact height
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 0, 15, 0) # Remove vertical padding
        
        lbl_title = QLabel("Designation & Levels")
        lbl_title.setStyleSheet("color: white; border: none; font-size: 18px; font-weight: bold;")
        
        btn_add_d = QPushButton("+ Add Designation")
        btn_add_d.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px; font-weight: bold;")
        btn_add_d.clicked.connect(self.add_designation_dialog)
        
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_add_d)
        
        layout.addWidget(header_widget)
        
        # Splitter for Designations (Left) and Subcategories (Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #444; }")
        layout.addWidget(splitter)
        
        # --- LEFT: Designations ---
        left_group = QGroupBox("Designations")
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(5, 10, 5, 5)
        
        self.table_deg = QTableWidget()
        self.table_deg.setColumnCount(2)
        self.table_deg.setHorizontalHeaderLabels(["ID", "Name"])
        self.table_deg.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_deg.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_deg.verticalHeader().setVisible(False)
        self.table_deg.itemSelectionChanged.connect(self.on_designation_selected)
        left_layout.addWidget(self.table_deg)
        
        splitter.addWidget(left_group)
        
        # --- RIGHT: Subcategories ---
        self.right_group = QGroupBox("Subcategories") # Dynamic title
        right_layout = QVBoxLayout(self.right_group)
        right_layout.setContentsMargins(5, 10, 5, 5)
        
        header_s = QHBoxLayout()
        header_s.addStretch()
        self.btn_add_s = QPushButton("+ Add Subcategory")
        self.btn_add_s.setStyleSheet("padding: 5px 10px;")
        self.btn_add_s.setEnabled(False)
        self.btn_add_s.clicked.connect(self.add_subcategory_dialog)
        header_s.addWidget(self.btn_add_s)
        right_layout.addLayout(header_s)
        
        self.table_sub = QTableWidget()
        self.table_sub.setColumnCount(2)
        self.table_sub.setHorizontalHeaderLabels(["ID", "Name"])
        self.table_sub.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_sub.verticalHeader().setVisible(False)
        right_layout.addWidget(self.table_sub)
        
        splitter.addWidget(self.right_group)
        splitter.setSizes([350, 450])
        
    def load_designations(self):
        session = get_db_session()
        designations = session.query(Designation).all()
        
        self.table_deg.setRowCount(0)
        for row, deg in enumerate(designations):
            self.table_deg.insertRow(row)
            self.table_deg.setItem(row, 0, QTableWidgetItem(str(deg.id)))
            self.table_deg.setItem(row, 1, QTableWidgetItem(deg.name))
            
    def on_designation_selected(self):
        selected_items = self.table_deg.selectedItems()
        if not selected_items:
            self.btn_add_s.setEnabled(False)
            self.table_sub.setRowCount(0)
            self.right_group.setTitle("Subcategories")
            return
            
        row = selected_items[0].row()
        deg_id = int(self.table_deg.item(row, 0).text())
        deg_name = self.table_deg.item(row, 1).text()
        
        self.right_group.setTitle(f"{deg_name} - Subcategories")
        self.btn_add_s.setEnabled(True)
        self.load_subcategories(deg_id)
        
    def load_subcategories(self, deg_id):
        session = get_db_session()
        subs = session.query(DesignationSubcategory).filter_by(designation_id=deg_id).all()
        
        self.table_sub.setRowCount(0)
        for row, sub in enumerate(subs):
            self.table_sub.insertRow(row)
            self.table_sub.setItem(row, 0, QTableWidgetItem(str(sub.id)))
            self.table_sub.setItem(row, 1, QTableWidgetItem(sub.name))

    def add_designation_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Designation")
        form = QFormLayout(dialog)
        
        name_input = QLineEdit()
        form.addRow("Name:", name_input)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(lambda: self.save_designation(dialog, name_input.text()))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_designation(self, dialog, name):
        if not name: return
        
        session = get_db_session()
        try:
            deg = Designation(name=name)
            session.add(deg)
            session.commit()
            dialog.accept()
            self.load_designations()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def add_subcategory_dialog(self):
        selected_items = self.table_deg.selectedItems()
        if not selected_items: return
        
        row = selected_items[0].row()
        deg_id = int(self.table_deg.item(row, 0).text())
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Subcategory")
        form = QFormLayout(dialog)
        
        name_input = QLineEdit()
        form.addRow("Name:", name_input)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(lambda: self.save_subcategory(dialog, deg_id, name_input.text()))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_subcategory(self, dialog, deg_id, name):
        if not name: return
        
        session = get_db_session()
        try:
            sub = DesignationSubcategory(name=name, designation_id=deg_id)
            session.add(sub)
            session.commit()
            dialog.accept()
            self.load_subcategories(deg_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
