from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView, QComboBox, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt
from database import get_db_session
from models import Designation, DesignationSubcategory
from ui.btn_styles import btn_primary, btn_neutral, btn_small_edit, btn_small_delete

class DesignationManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_designations()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # --- Top Header ---
        header_layout = QHBoxLayout()

        lbl_title = QLabel("Designation & Levels")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_designations)

        btn_add_d = QPushButton("+ Add Designation")
        btn_add_d.setStyleSheet(btn_primary())
        btn_add_d.clicked.connect(lambda: self.add_designation_dialog(None))

        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_refresh)
        header_layout.addWidget(btn_add_d)

        layout.addLayout(header_layout)
        
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
        self.table_deg.setColumnCount(3)

        self.table_deg.setHorizontalHeaderLabels(["ID", "Name", "Action"])
        self.table_deg.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_deg.verticalHeader().setDefaultSectionSize(36)
        self.table_deg.verticalHeader().hide()
        self.table_deg.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_deg.verticalHeader().setVisible(False)
        self.table_deg.itemSelectionChanged.connect(self.on_designation_selected)
        self.table_deg.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_deg.setColumnWidth(2, 160)
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
        self.btn_add_s.clicked.connect(lambda: self.add_subcategory_dialog(None))
        header_s.addWidget(self.btn_add_s)
        right_layout.addLayout(header_s)
        
        self.table_sub = QTableWidget()
        self.table_sub.setColumnCount(3)

        self.table_sub.setHorizontalHeaderLabels(["ID", "Name", "Action"])
        self.table_sub.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_sub.verticalHeader().setDefaultSectionSize(36)
        self.table_sub.verticalHeader().hide()
        self.table_sub.verticalHeader().setVisible(False)
        self.table_sub.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_sub.setColumnWidth(2, 160)
        right_layout.addWidget(self.table_sub)
        
        splitter.addWidget(self.right_group)
        splitter.setSizes([350, 450])
        
    def load_designations(self):
        session = get_db_session()
        designations = session.query(Designation).all()
        
        self.table_deg.setRowCount(0)
        # Clear subcat view as well on full reload
        self.table_sub.setRowCount(0)
        self.right_group.setTitle("Subcategories")
        self.btn_add_s.setEnabled(False)
            
        for row, deg in enumerate(designations):
            self.table_deg.insertRow(row)
            self.table_deg.setItem(row, 0, QTableWidgetItem(str(deg.id)))
            self.table_deg.setItem(row, 1, QTableWidgetItem(deg.name))
            
            # Action
            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = QPushButton("E")
            btn_edit.setStyleSheet(btn_small_edit())
            btn_edit.clicked.connect(lambda ch, x=deg: self.add_designation_dialog(x))
            action_layout.addWidget(btn_edit)
            
            btn_del = QPushButton("X")
            btn_del.setFixedWidth(30)
            btn_del.setStyleSheet(btn_small_delete())
            btn_del.clicked.connect(lambda ch, x=deg: self.delete_designation(x))
            action_layout.addWidget(btn_del)
            
            self.table_deg.setCellWidget(row, 2, action_widget)

    def load_data(self):
        """Alias for navigate() auto-refresh."""
        self.load_designations()
            
    def delete_designation(self, deg):
        confirm = QMessageBox.question(self, "Confirm", f"Delete designation '{deg.name}'? This will delete all subcategories too.", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(Designation).filter_by(id=deg.id).delete()
            session.commit()
            self.load_designations()
            
    def on_designation_selected(self):
        selected_items = self.table_deg.selectedItems()
        if not selected_items:
            # self.btn_add_s.setEnabled(False) # Don't disable immediately, might be just reload
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
            
            # Action
            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = QPushButton("E")
            btn_edit.setStyleSheet(btn_small_edit())
            btn_edit.clicked.connect(lambda ch, x=sub: self.add_subcategory_dialog(x))
            action_layout.addWidget(btn_edit)
            
            btn_del = QPushButton("X")
            btn_del.setFixedWidth(30)
            btn_del.setStyleSheet(btn_small_delete())
            btn_del.clicked.connect(lambda ch, x=sub: self.delete_subcategory(x))
            action_layout.addWidget(btn_del)
            
            self.table_sub.setCellWidget(row, 2, action_widget)

    def delete_subcategory(self, sub):
        confirm = QMessageBox.question(self, "Confirm", f"Delete subcategory '{sub.name}'?", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            designation_id = sub.designation_id
            session.query(DesignationSubcategory).filter_by(id=sub.id).delete()
            session.commit()
            self.load_subcategories(designation_id)

    def add_designation_dialog(self, deg_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Designation" if deg_obj else "Add Designation")
        form = QFormLayout(dialog)
        
        name_input = QLineEdit()
        if deg_obj: name_input.setText(deg_obj.name)
        
        form.addRow("Name:", name_input)
        
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_designation(dialog, deg_obj, name_input.text()))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_designation(self, dialog, deg_obj, name):
        if not name: return
        
        session = get_db_session()
        try:
            if deg_obj:
                d = session.get(Designation, deg_obj.id)
                d.name = name
            else:
                deg = Designation(name=name)
                session.add(deg)
            session.commit()
            dialog.accept()
            self.load_designations()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
 
    def add_subcategory_dialog(self, sub_obj=None):
        deg_id = None
        if not sub_obj:
            selected_items = self.table_deg.selectedItems()
            if not selected_items: return
            row = selected_items[0].row()
            deg_id = int(self.table_deg.item(row, 0).text())
        else:
            deg_id = sub_obj.designation_id
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Subcategory" if sub_obj else "Add Subcategory")
        form = QFormLayout(dialog)
        
        name_input = QLineEdit()
        if sub_obj: name_input.setText(sub_obj.name)
        
        form.addRow("Name:", name_input)
        
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(btn_primary())
        btn_save.clicked.connect(lambda: self.save_subcategory(dialog, sub_obj, deg_id, name_input.text()))
        form.addRow(btn_save)
        
        dialog.exec()
        
    def save_subcategory(self, dialog, sub_obj, deg_id, name):
        if not name: return
        
        session = get_db_session()
        try:
            if sub_obj:
                s = session.get(DesignationSubcategory, sub_obj.id)
                s.name = name
            else:
                sub = DesignationSubcategory(name=name, designation_id=deg_id)
                session.add(sub)
            session.commit()
            dialog.accept()
            # self.load_subcategories(deg_id) # Might need to refresh manually or triggered by selection?
            # Since selection triggers load, calling load here is fine.
            self.load_subcategories(deg_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
