from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QFrame
)
from PyQt6.QtCore import Qt, QDate
from database import get_db_session
from models import SystemLog, AdminUser, Company, BusinessArea
from ui.btn_styles import btn_primary, btn_neutral
from ui.page_helpers import make_page_header, apply_table_defaults
import json

class SystemLogsManager(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.refresh_filters()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        btn_refresh = QPushButton("⟳  Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)
        
        layout.addWidget(make_page_header(
            "System Logs",
            "Audit trail of structural and administrative changes",
            extra_widgets=[btn_refresh]
        ))

        # Filter Bar
        filter_frame = QFrame()
        filter_frame.setObjectName("filter_frame")
        filter_frame.setStyleSheet("QFrame#filter_frame { background: transparent; }")
        
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(20, 10, 20, 10)
        fl.setSpacing(10)
        
        # Company Filter
        fl.addWidget(QLabel("Company:"))
        self.company_combo = QComboBox()
        self.company_combo.setMinimumWidth(120)
        fl.addWidget(self.company_combo)

        # Area Filter
        fl.addWidget(QLabel("Area:"))
        self.ba_combo = QComboBox()
        self.ba_combo.setMinimumWidth(120)
        fl.addWidget(self.ba_combo)

        # User Filter
        fl.addWidget(QLabel("User:"))
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(100)
        fl.addWidget(self.user_combo)
        
        # Date Range
        today = QDate.currentDate()
        month_start = QDate(today.year(), today.month(), 1)
        month_end = QDate(today.year(), today.month(), today.daysInMonth())

        fl.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(month_start)
        fl.addWidget(self.date_from)

        fl.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(month_end)
        fl.addWidget(self.date_to)

        btn_search = QPushButton("Apply Filters")
        btn_search.setMinimumWidth(110)
        btn_search.setStyleSheet(btn_primary())
        btn_search.clicked.connect(self.load_data)
        fl.addWidget(btn_search)

        fl.addStretch()
        layout.addWidget(filter_frame)


        # Table
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Entity", "ID", "Details"
        ])
        apply_table_defaults(
            self.table,
            stretch_cols=[5],
            fixed_cols={0: 160, 1: 100, 2: 80, 3: 120, 4: 60}
        )
        cl.addWidget(self.table)
        layout.addWidget(content, stretch=1)

    def refresh_filters(self):
        session = get_db_session()
        
        # Populate Company
        self.company_combo.clear()
        self.company_combo.addItem("All Companies", None)
        for c in session.query(Company).all():
            self.company_combo.addItem(c.name, c.id)

        # Populate User
        self.user_combo.clear()
        self.user_combo.addItem("All Users", None)
        for u in session.query(AdminUser).all():
            self.user_combo.addItem(u.username, u.id)

        # Update Business Area based on Company
        def update_ba():
            self.ba_combo.clear()
            self.ba_combo.addItem("All Areas", None)
            cid = self.company_combo.currentData()
            if cid:
                for ba in session.query(BusinessArea).filter_by(company_id=cid).all():
                    self.ba_combo.addItem(ba.name, ba.id)
        
        self.company_combo.currentIndexChanged.connect(update_ba)
        update_ba()

    def load_data(self):
        session = get_db_session()
        query = session.query(SystemLog).order_by(SystemLog.timestamp.desc())

        # Apply Filters
        user_id = self.user_combo.currentData()
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)

        # Date Range
        start_date = self.date_from.date().toPyDate()
        end_date = self.date_to.date().toPyDate()
        
        # We need to filter timestamp range. 
        # Since timestamp is DateTime, we want From 00:00:00 to 23:59:59
        from datetime import datetime, time
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        
        query = query.filter(SystemLog.timestamp >= start_dt, SystemLog.timestamp <= end_dt)

        # Company / Business Area filtering is more complex because SystemLog doesn't have these columns directly.
        # We need to filter based on the 'details' JSON or the entity relation if possible.
        # But structural logs usually refer to entities.
        # The request said "filter option like company, user, business area".
        # This implies we should filter logs where the entity BELONGS to that company/area.
        
        cid = self.company_combo.currentData()
        ba_id = self.ba_combo.currentData()

        # This part is tricky because logs are polymorphic. 
        # For simplicity, we can inspect the 'details' JSON which often contains company_id/business_area_id
        # or we join with the target table if we know it.
        # However, a robust way is to filter the in-memory or use JSON functions if SQLite supports them.
        
        logs = query.all()
        
        # Post-filter for Company/Area if selected
        if cid or ba_id:
            filtered_logs = []
            for log in logs:
                try:
                    details = json.loads(log.details)
                    match = True
                    if cid:
                        # Check details for company_id (Created) or company_id.new/old (Updated)
                        found_cid = details.get('company_id')
                        if isinstance(found_cid, dict): found_cid = found_cid.get('new')
                        if found_cid != cid: match = False
                    if ba_id and match:
                        found_baid = details.get('business_area_id')
                        if isinstance(found_baid, dict): found_baid = found_baid.get('new')
                        if found_baid != ba_id: match = False
                    if match:
                        filtered_logs.append(log)
                except:
                    # If we can't parse or it doesn't have the field, we exclude it from the specific filter
                    pass
            logs = filtered_logs

        self.table.setRowCount(0)
        for row, log in enumerate(logs):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(log.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(row, 1, QTableWidgetItem(log.user.username if log.user else "System"))
            self.table.setItem(row, 2, QTableWidgetItem(log.action_type))
            self.table.setItem(row, 3, QTableWidgetItem(log.entity_type))
            self.table.setItem(row, 4, QTableWidgetItem(str(log.entity_id) if log.entity_id else "-"))
            
            # Formatted Details
            try:
                raw_details = json.loads(log.details)
                if log.action_type == "Updated":
                    desc_list = [f"{k}: {v['old']} → {v['new']}" for k, v in raw_details.items()]
                    desc = " | ".join(desc_list)
                else:
                    # For Created/Deleted, show a summary of key fields
                    # Just show everything but truncated?
                    desc = str(raw_details)
            except:
                desc = log.details or ""
            
            detail_item = QTableWidgetItem(desc)
            detail_item.setToolTip(desc)
            self.table.setItem(row, 5, detail_item)
