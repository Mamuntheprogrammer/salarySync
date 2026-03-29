from ui.btn_styles import btn_primary, btn_neutral, btn_danger, btn_info
import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QMessageBox, QFrame, QSpinBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QFont
from database import get_db_session
from models import Employee, Company, BusinessArea
from services.face_service import FaceService
from config import Config
from ui.page_helpers import make_page_header


class FaceManager(QWidget):
    def __init__(self):
        super().__init__()
        self.camera = None
        self.current_frame = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_camera_running = False
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(make_page_header("Face Registration Manager",
                                         "Register and manage employee face profiles for attendance"))

        body = QWidget()
        main_layout = QHBoxLayout(body)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 16, 20, 16)
        outer.addWidget(body, stretch=1)
        
        # Left Side: Camera Box
        camera_container = QFrame()
        camera_container.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(20, 20, 20, 20)
        
        cam_title = QLabel("Registration Camera")
        cam_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cam_title.setFont(self.get_font(16, True))
        cam_title.setStyleSheet("border: none; margin-bottom: 10px;")
        camera_layout.addWidget(cam_title)
        
        self.video_label = QLabel("Camera Offline")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(400, 300)
        self.video_label.setStyleSheet("background-color: #111; color: #fff; font-size: 18px; border-radius: 8px;")
        
        video_wrap = QHBoxLayout()
        video_wrap.addWidget(self.video_label)
        camera_layout.addLayout(video_wrap)
        
        self.lbl_face_status = QLabel("Ready to capture new employee face.")
        self.lbl_face_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_face_status.setStyleSheet("color: #666; font-size: 14px; font-weight: bold; border: none; margin-top: 10px;")
        camera_layout.addWidget(self.lbl_face_status)
        
        # Action Buttons for Camera
        self.btn_toggle_cam = QPushButton("Turn On Camera")
        self.btn_toggle_cam.setStyleSheet(btn_info())
        self.btn_toggle_cam.clicked.connect(self.toggle_camera)
        
        btn_wrap = QHBoxLayout()
        btn_wrap.addStretch()
        btn_wrap.addWidget(self.btn_toggle_cam)
        btn_wrap.addStretch()
        camera_layout.addLayout(btn_wrap)
        camera_layout.addStretch()
        
        main_layout.addWidget(camera_container, stretch=1)
        
        # Right Side: Selection Box & Settings
        selection_container = QFrame()
        selection_container.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        selection_layout = QVBoxLayout(selection_container)
        selection_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Settings Section ---
        settings_title = QLabel("Registration Settings")
        settings_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_title.setFont(self.get_font(16, True))
        settings_title.setStyleSheet("border: none; margin-bottom: 5px;")
        selection_layout.addWidget(settings_title)
        
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Auto Clock-In Hold Time (s):"))
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(1, 15)
        self.delay_spinbox.setStyleSheet("padding: 5px; font-size: 14px;")
        config = Config.load_config()
        self.delay_spinbox.setValue(config.get("face_recognition", {}).get("auto_clock_delay_seconds", 3))
        
        self.btn_save_settings = QPushButton("Save Delay")
        self.btn_save_settings.setStyleSheet(btn_neutral())
        self.btn_save_settings.clicked.connect(self.save_settings)
        
        settings_layout.addWidget(self.delay_spinbox)
        settings_layout.addWidget(self.btn_save_settings)
        settings_layout.addStretch()
        selection_layout.addLayout(settings_layout)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        selection_layout.addWidget(line)
        
        # --- Selection & Filter Section ---
        sel_title = QLabel("Select Employee")
        sel_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sel_title.setFont(self.get_font(16, True))
        sel_title.setStyleSheet("border: none; margin-bottom: 15px; margin-top: 10px;")
        selection_layout.addWidget(sel_title)
        
        filter_layout = QHBoxLayout()
        self.company_combo = QComboBox()
        self.company_combo.currentIndexChanged.connect(self.load_business_areas)
        
        self.ba_combo = QComboBox()
        self.ba_combo.currentIndexChanged.connect(self.load_employees)
        
        filter_layout.addWidget(self.company_combo)
        filter_layout.addWidget(self.ba_combo)
        selection_layout.addLayout(filter_layout)
        
        self.emp_combo = QComboBox()
        self.emp_combo.setStyleSheet("""
            QComboBox {
                padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;
                background-color: #f9f9f9; margin-top: 10px;
            }
        """)
        selection_layout.addWidget(self.emp_combo)
        
        self.btn_refresh = QPushButton("⟳  Refresh List")
        self.btn_refresh.setStyleSheet(btn_neutral())
        self.btn_refresh.clicked.connect(self.load_companies)
        
        refresh_wrap = QHBoxLayout()
        refresh_wrap.addStretch()
        refresh_wrap.addWidget(self.btn_refresh)
        selection_layout.addLayout(refresh_wrap)
        
        selection_layout.addStretch()
        
        self.btn_capture = QPushButton("Capture & Register Face")
        self.btn_capture.setStyleSheet(btn_primary())
        self.btn_capture.clicked.connect(self.capture_face)
        self.btn_capture.setEnabled(False)
        selection_layout.addWidget(self.btn_capture)
        
        self.btn_delete = QPushButton("Delete Face Data")
        self.btn_delete.setStyleSheet(btn_danger())
        self.btn_delete.clicked.connect(self.delete_face)
        selection_layout.addWidget(self.btn_delete)

        main_layout.addWidget(selection_container, stretch=1)

        self.load_companies()
        
    def get_font(self, size, bold=False):
        from PyQt6.QtGui import QFont
        font = QFont("Arial", size)
        font.setBold(bold)
        return font
        
    def load_companies(self):
        self.company_combo.blockSignals(True)
        self.company_combo.clear()
        self.company_combo.addItem("All Companies", None)
        session = get_db_session()
        companies = session.query(Company).all()
        for c in companies:
            self.company_combo.addItem(c.name, c.id)
        session.close()
        self.company_combo.blockSignals(False)
        self.load_business_areas()

    def load_data(self):
        """Auto-refresh hook — reload employee dropdowns without touching camera."""
        self.load_companies()

    def load_business_areas(self):
        comp_id = self.company_combo.currentData()
        self.ba_combo.blockSignals(True)
        self.ba_combo.clear()
        self.ba_combo.addItem("All Business Areas", None)
        
        session = get_db_session()
        query = session.query(BusinessArea)
        if comp_id:
            query = query.filter(BusinessArea.company_id == comp_id)
        
        bas = query.all()
        for b in bas:
            self.ba_combo.addItem(b.name, b.id)
        session.close()
        self.ba_combo.blockSignals(False)
        self.load_employees()

    def load_employees(self):
        self.emp_combo.clear()
        self.emp_combo.addItem("Select Employee...", None)
        
        comp_id = self.company_combo.currentData()
        ba_id = self.ba_combo.currentData()
        
        session = get_db_session()
        query = session.query(Employee).filter(Employee.is_active == True)
        if comp_id:
            query = query.filter(Employee.company_id == comp_id)
        if ba_id:
            query = query.filter(Employee.business_area_id == ba_id)
            
        employees = query.all()
        for emp in employees:
            status = "✅ Registered" if emp.face_encoding_path else "❌ Not Registered"
            text = f"[{emp.id}] {emp.full_name} ({status})"
            self.emp_combo.addItem(text, emp.id)
        session.close()

    def save_settings(self):
        val = self.delay_spinbox.value()
        config = Config.load_config()
        if "face_recognition" not in config:
            config["face_recognition"] = {}
        config["face_recognition"]["auto_clock_delay_seconds"] = val
        if Config.save_config(config):
            QMessageBox.information(self, "Success", "Registration settings saved. Terminal will update on next launch.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save settings.")

    def delete_face(self):
        emp_id = self.emp_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "Error", "Please select an employee first.")
            return
            
        reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to remove this face profile?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                                     
        if reply == QMessageBox.StandardButton.Yes:
            session = get_db_session()
            emp = session.query(Employee).get(emp_id)
            if emp:
                res, msg = FaceService.delete_encoding(session, emp)
                if res:
                    QMessageBox.information(self, "Success", msg)
                    self.load_employees()
                else:
                    QMessageBox.warning(self, "Warning", msg)
            session.close()
            
    def toggle_camera(self):
        if not self.is_camera_running:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QMessageBox.warning(self, "Error", "Could not access the webcam.")
                return
            self.is_camera_running = True
            self.btn_toggle_cam.setText("Turn Off Camera")
            self.btn_toggle_cam.setStyleSheet(btn_danger())
            self.btn_capture.setEnabled(True)
            self.timer.start(30)
        else:
            self.stop_camera()
            
    def stop_camera(self):
        self.is_camera_running = False
        self.timer.stop()
        if self.camera:
            self.camera.release()
            self.camera = None
        self.video_label.clear()
        self.video_label.setText("Camera Offline")
        self.btn_toggle_cam.setText("Turn On Camera")
        self.btn_toggle_cam.setStyleSheet(btn_info())
        self.btn_capture.setEnabled(False)
        self.current_frame = None

    def update_frame(self):
        if not self.camera:
            return
            
        ret, frame = self.camera.read()
        if ret:
            # OpenCV brings BGR, convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.current_frame = rgb_frame # Store for capture
            
            # Convert to QImage and display
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale to fit label while keeping aspect ratio
            scaled_pixmap = pixmap.scaled(self.video_label.width(), self.video_label.height(), Qt.AspectRatioMode.KeepAspectRatio)
            self.video_label.setPixmap(scaled_pixmap)

    def capture_face(self):
        emp_id = self.emp_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "Error", "Please select an employee first.")
            return
            
        if self.current_frame is None:
            QMessageBox.warning(self, "Error", "No camera frame available.")
            return
            
        session = get_db_session()
        employee = session.query(Employee).get(emp_id)
        if not employee:
            QMessageBox.critical(self, "Error", "Employee not found.")
            return

        # Pause UI slightly
        self.btn_capture.setText("Processing...")
        self.btn_capture.setEnabled(False)
        
        # Use FaceService
        success, message = FaceService.save_encoding(session, employee, self.current_frame)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.load_employees() # Refresh list to show checkbox
        else:
            QMessageBox.warning(self, "Warning", message)
            
        self.btn_capture.setText("Capture & Register Face")
        self.btn_capture.setEnabled(True)
        
    def hideEvent(self, event):
        # Stop camera if switching away from this tab
        self.stop_camera()
        super().hideEvent(event)
