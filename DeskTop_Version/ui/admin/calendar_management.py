from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QDialog, 
                             QLineEdit, QFormLayout, QMessageBox, QHeaderView, QComboBox, 
                             QDateEdit, QCheckBox, QTabWidget, QSpinBox, QFileDialog, QRadioButton, QButtonGroup)
from PyQt6.QtCore import QDate, Qt
from database import get_db_session
from models import HolidayCalendar, WeeklyHoliday, BusinessArea, Employee, Company
from datetime import datetime
import csv

class CalendarManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(QLabel("<h2>Holiday & Weekly Off Manager</h2>"))
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_holiday_tab(), "Public Holidays")
        self.tabs.addTab(self.create_weekly_tab(), "Weekly Holidays")
        
        layout.addWidget(self.tabs)
        
        # Initial Load
        self.load_holidays()
        self.load_weekly()

    def load_data(self):
        """Auto-refresh hook called by navigate()."""
        self.load_holidays()
        self.load_weekly()

    # --- TAB 1: Public Holidays ---
    def create_holiday_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tools
        tools = QHBoxLayout()
        
        self.year_filter = QComboBox()
        current_year = datetime.now().year
        self.year_filter.addItems([str(y) for y in range(current_year-2, current_year+5)])
        self.year_filter.setCurrentText(str(current_year))
        self.year_filter.currentTextChanged.connect(self.load_holidays)
        
        tools.addWidget(QLabel("Year:"))
        tools.addWidget(self.year_filter)
        tools.addStretch()
        
        btn_add = QPushButton("Add Holiday")
        btn_add.clicked.connect(lambda: self.add_holiday_dialog(holiday_obj=None))
        tools.addWidget(btn_add)
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_holidays)
        tools.addWidget(btn_refresh)
        
        btn_upload = QPushButton("Upload CSV")
        btn_upload.clicked.connect(self.upload_holiday_csv)
        tools.addWidget(btn_upload)
        
        layout.addLayout(tools)
        
        # Table
        self.hol_table = QTableWidget()
        self.hol_table.setColumnCount(7)
        self.hol_table.setHorizontalHeaderLabels(["Date", "Description", "Type", "Company Code", "Business Area", "OT Eligible", "Action"])
        self.hol_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.hol_table)
        
        return widget
        
    def load_holidays(self):
        year = int(self.year_filter.currentText())
        session = get_db_session()
        holidays = session.query(HolidayCalendar).filter_by(year=year).order_by(HolidayCalendar.date).all()
        
        self.hol_table.setRowCount(0)
        for row, h in enumerate(holidays):
            self.hol_table.insertRow(row)
            self.hol_table.setItem(row, 0, QTableWidgetItem(h.date.strftime("%Y-%m-%d")))
            self.hol_table.setItem(row, 1, QTableWidgetItem(h.description))
            self.hol_table.setItem(row, 2, QTableWidgetItem(h.type))
            
            comp_val = h.company.name if h.company else "Global"
            ba_val = h.business_area.name if h.business_area else "All"
            
            self.hol_table.setItem(row, 3, QTableWidgetItem(comp_val))
            self.hol_table.setItem(row, 4, QTableWidgetItem(ba_val))
            
            self.hol_table.setItem(row, 5, QTableWidgetItem("Yes" if h.is_ot_eligible else "No"))
            
            # Action Column with Edit/Delete
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda ch, x=h: self.add_holiday_dialog(holiday_obj=x))
            action_layout.addWidget(btn_edit)
            
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet("color: red")
            btn_del.clicked.connect(lambda ch, x=h: self.delete_holiday(x))
            action_layout.addWidget(btn_del)
            
            self.hol_table.setCellWidget(row, 6, action_widget)
            
    def upload_holiday_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Upload Holiday CSV", "", "CSV Files (*.csv)")
        if not path: return
        
        session = get_db_session()
        try:
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                # Expected: Date, Description, Type, OT Eligible
                
                count = 0
                for row in reader:
                    # Parse Date
                    date_str = row.get("Date")
                    if not date_str: continue
                    
                    try:
                        h_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        continue # Skip invalid dates
                        
                    desc = row.get("Description", "Holiday")
                    h_type = row.get("Type", "National")
                    ot_raw = row.get("OT Eligible", "No").lower()
                    is_ot = ot_raw in ["yes", "true", "1", "y"]
                    
                    # Check exist
                    exists = session.query(HolidayCalendar).filter_by(date=h_date).first()
                    if exists:
                        exists.description = desc
                        exists.type = h_type
                        exists.is_ot_eligible = is_ot
                    else:
                        h = HolidayCalendar(
                            date=h_date,
                            year=h_date.year,
                            description=desc,
                            type=h_type,
                            is_ot_eligible=is_ot,
                            company_id=None, # Global
                            business_area_id=None
                        )
                        session.add(h)
                    count += 1
                
                session.commit()
                QMessageBox.information(self, "Success", f"Imported/Updated {count} holidays.")
                self.load_holidays()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import: {str(e)}")

    def add_holiday_dialog(self, holiday_obj=None):
        session = get_db_session()
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Holiday")
        form = QFormLayout(dialog)
        
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        
        desc_input = QLineEdit()
        
        type_input = QComboBox()
        type_input.setEditable(True)
        type_input.addItems(["National", "Festival", "Company", "Other"])
        
        ot_input = QCheckBox("OT Eligible")
        
        # Scope Selection
        comp_input = QComboBox()
        comp_input.addItem("All Companies (Global)", None)
        comps = session.query(Company).all()
        for c in comps: comp_input.addItem(c.name, c.id)
        
        ba_input = QComboBox()
        ba_input.addItem("All Business Areas", None)
        ba_input.setEnabled(False)
        
        def on_comp_change():
            ba_input.clear()
            ba_input.addItem("All Business Areas", None)
            ba_input.setEnabled(False)
            
            comp_id = comp_input.currentData()
            if comp_id:
                bas = session.query(BusinessArea).filter_by(company_id=comp_id).all()
                for ba in bas: ba_input.addItem(ba.name, ba.id)
                ba_input.setEnabled(True)
                
        comp_input.currentIndexChanged.connect(on_comp_change)
        
        # Pre-fill if editing
        if holiday_obj:
            dialog.setWindowTitle("Edit Holiday")
            date_input.setDate(holiday_obj.date)
            desc_input.setText(holiday_obj.description)
            type_input.setCurrentText(holiday_obj.type)
            ot_input.setChecked(holiday_obj.is_ot_eligible)
            
            if holiday_obj.company_id:
                index = comp_input.findData(holiday_obj.company_id)
                if index >= 0: comp_input.setCurrentIndex(index)
                
            # Trigger logic to fill BA
            if holiday_obj.business_area_id:
                # Wait for BA combo to populate
                index = ba_input.findData(holiday_obj.business_area_id)
                if index >= 0: ba_input.setCurrentIndex(index)
        
        form.addRow("Date:", date_input)
        form.addRow("Description:", desc_input)
        form.addRow("Type:", type_input)
        form.addRow("OT Eligible:", ot_input)
        form.addRow("Company:", comp_input)
        form.addRow("Business Area:", ba_input)
        
        btn_save = QPushButton("Save")
        def save():
            if not desc_input.text(): 
                QMessageBox.warning(dialog, "Warning", "Description is required")
                return
            
            comp_id = comp_input.currentData()
            ba_id = ba_input.currentData()

            h_date = date_input.date().toPyDate()
            year = h_date.year
            
            # Check for existing holiday on same date/scope to avoid duplicates?
            # For now, just save.
            
            if holiday_obj:
                # Update existing
                holiday_obj.date = h_date
                holiday_obj.year = year
                holiday_obj.description = desc_input.text()
                holiday_obj.type = type_input.currentText()
                holiday_obj.is_ot_eligible = ot_input.isChecked()
                holiday_obj.company_id = comp_id
                holiday_obj.business_area_id = ba_id
            else:
                h = HolidayCalendar(
                    date=h_date,
                    year=year,
                    description=desc_input.text(),
                    type=type_input.currentText(),
                    is_ot_eligible=ot_input.isChecked(),
                    company_id=comp_id,
                    business_area_id=ba_id
                )
                session.add(h)
            
            try:
                session.commit()
                dialog.accept()
                self.load_holidays()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(dialog, "Error", str(e))
                
        btn_save.clicked.connect(save)
        form.addRow(btn_save)
        dialog.exec()

    def delete_holiday(self, holiday):
        confirm = QMessageBox.question(self, "Confirm", "Delete this holiday?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(HolidayCalendar).filter_by(id=holiday.id).delete()
            session.commit()
            self.load_holidays()

    # --- TAB 2: Weekly Holidays ---
    def create_weekly_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        tools = QHBoxLayout()
        btn_add = QPushButton("Add Weekly Rule")
        btn_add.clicked.connect(self.add_weekly_dialog)
        tools.addWidget(btn_add)
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_weekly)
        tools.addWidget(btn_refresh)
        
        tools.addStretch()
        layout.addLayout(tools)
        
        self.weekly_table = QTableWidget()
        self.weekly_table.setColumnCount(4)
        self.weekly_table.setHorizontalHeaderLabels(["Scope", "Day", "Target", "Action"])
        self.weekly_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.weekly_table)
        
        return widget

    def load_weekly(self):
        session = get_db_session()
        rules = session.query(WeeklyHoliday).all()
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        self.weekly_table.setRowCount(0)
        for row, r in enumerate(rules):
            self.weekly_table.insertRow(row)
            
            target = "Global?" 
            scope = "Unknown"
            
            if r.company:
                scope = "Company"
                target = r.company.name
            if r.business_area:
                scope = "Business Area"
                target = r.business_area.name
            elif r.shift:
                scope = "Shift"
                target = r.shift.name
            
            self.weekly_table.setItem(row, 0, QTableWidgetItem(scope))
            self.weekly_table.setItem(row, 1, QTableWidgetItem(days[r.day_of_week]))
            self.weekly_table.setItem(row, 2, QTableWidgetItem(target))
            
            # Action Column with Edit/Delete
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda ch, x=r: self.add_weekly_dialog(weekly_obj=x))
            action_layout.addWidget(btn_edit)
            
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet("color: red")
            btn_del.clicked.connect(lambda ch, x=r: self.delete_weekly(x))
            action_layout.addWidget(btn_del)
            
            self.weekly_table.setCellWidget(row, 3, action_widget)

    def add_weekly_dialog(self, weekly_obj=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Weekly Holiday Rule" if weekly_obj else "Add Weekly Holiday Rule")
        form = QFormLayout(dialog)
        
        day_input = QComboBox()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_input.addItems(days)
        
        from models import Company, Shift
        session = get_db_session()
        
        # Scope Selection
        scope_layout = QHBoxLayout()
        rb_org = QRadioButton("Organization (Company/BA)")
        rb_shift = QRadioButton("Shift")
        rb_org.setChecked(True)
        
        scope_group = QButtonGroup(dialog)
        scope_group.addButton(rb_org)
        scope_group.addButton(rb_shift)
        
        scope_layout.addWidget(rb_org)
        scope_layout.addWidget(rb_shift)
        
        # Inputs
        comp_input = QComboBox()
        comp_input.addItem("All Companies (Global)", None)
        comps = session.query(Company).all()
        for c in comps: comp_input.addItem(c.name, c.id)
        
        ba_input = QComboBox()
        ba_input.addItem("All Business Areas", None)
        ba_input.setEnabled(False)
        
        shift_input = QComboBox()
        shift_input.addItem("Select Shift...", None)
        shifts = session.query(Shift).all()
        for s in shifts: shift_input.addItem(s.name, s.id)
        shift_input.setEnabled(False) # Initially disabled
        
        def toggle_mode():
            is_org = rb_org.isChecked()
            comp_input.setEnabled(is_org)
            ba_input.setEnabled(is_org and comp_input.currentData() is not None)
            shift_input.setEnabled(not is_org)
            
        rb_org.toggled.connect(toggle_mode)
        rb_shift.toggled.connect(toggle_mode)
        
        def on_comp_change():
            ba_input.clear()
            ba_input.addItem("All Business Areas", None)
            ba_input.setEnabled(False)
            
            comp_id = comp_input.currentData()
            if comp_id:
                bas = session.query(BusinessArea).filter_by(company_id=comp_id).all()
                for ba in bas: ba_input.addItem(ba.name, ba.id)
                ba_input.setEnabled(True)
                
        comp_input.currentIndexChanged.connect(on_comp_change)
        
        # Pre-fill if editing
        if weekly_obj:
            day_input.setCurrentIndex(weekly_obj.day_of_week)
            
            if weekly_obj.shift_id:
                rb_shift.setChecked(True)
                toggle_mode() # Update enabled states
                idx = shift_input.findData(weekly_obj.shift_id)
                if idx >= 0: shift_input.setCurrentIndex(idx)
            else:
                rb_org.setChecked(True)
                toggle_mode()
                
                if weekly_obj.company_id:
                    idx = comp_input.findData(weekly_obj.company_id)
                    if idx >= 0: comp_input.setCurrentIndex(idx)
                    
                    # Wait/Trigger population of BA
                    # on_comp_change called automatically or need manual? 
                    # currentIndexChanged usually fires on programmatic change if signals not blocked.
                    # Just in case, let's manually trigger logic if BA needs setting
                    
                    if weekly_obj.business_area_id:
                         # Ensure items populated (on_comp_change triggers on index change)
                         # If index didn't change (e.g. was already 0), might need explicit call?
                         # But index likely changed if company_id present. 
                         # Let's verify BA is set.
                         idx_ba = ba_input.findData(weekly_obj.business_area_id)
                         if idx_ba >= 0: ba_input.setCurrentIndex(idx_ba)

        form.addRow("Mode:", scope_layout)
        form.addRow("Day:", day_input)
        form.addRow("Company:", comp_input)
        form.addRow("Business Area:", ba_input)
        form.addRow("Shift:", shift_input)
        
        btn_save = QPushButton("Save")
        def save():
            day_idx = day_input.currentIndex()
            
            comp_id = None
            ba_id = None
            shift_id = None
            
            if rb_org.isChecked():
                comp_id = comp_input.currentData()
                ba_id = ba_input.currentData()
            else:
                shift_id = shift_input.currentData()
                if not shift_id:
                    QMessageBox.warning(dialog, "Missing Input", "Please select a shift.")
                    return
            
            if weekly_obj:
                weekly_obj.day_of_week = day_idx
                weekly_obj.company_id = comp_id
                weekly_obj.business_area_id = ba_id
                weekly_obj.shift_id = shift_id
            else:
                w = WeeklyHoliday(
                    day_of_week=day_idx,
                    company_id=comp_id,
                    business_area_id=ba_id,
                    shift_id=shift_id
                )
                session.add(w)
                
            try:
                session.commit()
                dialog.accept()
                self.load_weekly()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", str(e))
                
        btn_save.clicked.connect(save)
        form.addRow(btn_save)
        dialog.exec()
        
    def delete_weekly(self, rule):
        confirm = QMessageBox.question(self, "Confirm", "Delete this rule?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            session.query(WeeklyHoliday).filter_by(id=rule.id).delete()
            session.commit()
            self.load_weekly()

            self.load_weekly()
