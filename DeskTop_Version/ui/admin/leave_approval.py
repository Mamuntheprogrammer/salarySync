from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem,
                             QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QDate
from database import get_db_session
from models import LeaveRequest, ShortLeave
from services.leave_service import LeaveService
from config import Config
from ui.btn_styles import btn_small_approve, btn_small_reject, btn_neutral
from ui.page_helpers import make_page_header, apply_table_defaults


class LeaveApproval(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        btn_refresh = QPushButton("⟳  Refresh")
        btn_refresh.setStyleSheet(btn_neutral())
        btn_refresh.clicked.connect(self.load_data)

        layout.addWidget(make_page_header("Leave Approval",
                                          "Review and approve pending leave requests",
                                          extra_widgets=[btn_refresh]))

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._make_full_tab(), "Full Leaves (Pending)")
        self.tabs.addTab(self._make_short_tab(), "Short Leaves (Pending)")
        cl.addWidget(self.tabs)
        layout.addWidget(content, stretch=1)

        self.load_data()

    def _make_full_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        self.full_table = QTableWidget()
        self.full_table.setColumnCount(7)
        self.full_table.setHorizontalHeaderLabels(["ID", "Employee", "Type", "Start", "End", "Reason", "Actions"])
        apply_table_defaults(self.full_table,
                             stretch_cols=[1, 5],
                             fixed_cols={0: 40, 2: 100, 3: 90, 4: 90, 6: 160})
        lay.addWidget(self.full_table)
        return w

    def _make_short_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        self.short_table = QTableWidget()
        self.short_table.setColumnCount(7)
        self.short_table.setHorizontalHeaderLabels(["ID", "Employee", "Date", "Start", "End", "Reason", "Actions"])
        apply_table_defaults(self.short_table,
                             stretch_cols=[1, 5],
                             fixed_cols={0: 40, 2: 90, 3: 80, 4: 80, 6: 160})
        lay.addWidget(self.short_table)
        return w

    def load_data(self):
        session = get_db_session()
        time_fmt = Config.get_time_fmt()

        # Full leaves
        pending_full = session.query(LeaveRequest).filter_by(status='Pending').all()
        self.tabs.setTabText(0, f"Full Leaves ({len(pending_full)} Pending)")
        self.full_table.setRowCount(0)
        for row, req in enumerate(pending_full):
            self.full_table.insertRow(row)
            self.full_table.setItem(row, 0, QTableWidgetItem(str(req.id)))
            self.full_table.setItem(row, 1, QTableWidgetItem(f"{req.employee.id} — {req.employee.full_name}"))
            self.full_table.setItem(row, 2, QTableWidgetItem(req.leave_type))
            self.full_table.setItem(row, 3, QTableWidgetItem(str(req.start_date)))
            self.full_table.setItem(row, 4, QTableWidgetItem(str(req.end_date)))
            self.full_table.setItem(row, 5, QTableWidgetItem(req.reason))
            self.full_table.setCellWidget(row, 6, self._approve_reject_widget(
                lambda _, r=req: self.approve_full(r),
                lambda _, r=req: self.reject_full(r)
            ))

        # Short leaves
        pending_short = session.query(ShortLeave).filter_by(status='Pending').all()
        self.tabs.setTabText(1, f"Short Leaves ({len(pending_short)} Pending)")
        self.short_table.setRowCount(0)
        for row, req in enumerate(pending_short):
            self.short_table.insertRow(row)
            self.short_table.setItem(row, 0, QTableWidgetItem(str(req.id)))
            self.short_table.setItem(row, 1, QTableWidgetItem(f"{req.employee.id} — {req.employee.full_name}"))
            self.short_table.setItem(row, 2, QTableWidgetItem(str(req.date)))
            self.short_table.setItem(row, 3, QTableWidgetItem(req.start_time.strftime(time_fmt)))
            self.short_table.setItem(row, 4, QTableWidgetItem(req.end_time.strftime(time_fmt)))
            self.short_table.setItem(row, 5, QTableWidgetItem(req.reason))
            self.short_table.setCellWidget(row, 6, self._approve_reject_widget(
                lambda _, r=req: self.approve_short(r),
                lambda _, r=req: self.reject_short(r)
            ))

    def _approve_reject_widget(self, approve_fn, reject_fn):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(4)
        b1 = QPushButton("Approve")
        b1.setStyleSheet(btn_small_approve())
        b1.clicked.connect(approve_fn)
        b2 = QPushButton("Reject")
        b2.setStyleSheet(btn_small_reject())
        b2.clicked.connect(reject_fn)
        h.addWidget(b1)
        h.addWidget(b2)
        return w

    def approve_full(self, req):
        res = LeaveService.approve_request(get_db_session(), req.id, "admin")
        QMessageBox.information(self, "Result", res['message'])
        self.load_data()

    def reject_full(self, req):
        res = LeaveService.reject_request(get_db_session(), req.id, "Rejected by Admin")
        QMessageBox.information(self, "Result", res['message'])
        self.load_data()

    def approve_short(self, req):
        res = LeaveService.approve_short_leave(get_db_session(), req.id)
        QMessageBox.information(self, "Result", res['message'])
        self.load_data()

    def reject_short(self, req):
        res = LeaveService.reject_short_leave(get_db_session(), req.id)
        QMessageBox.information(self, "Result", res['message'])
        self.load_data()
