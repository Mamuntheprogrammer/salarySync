from PyQt6.QtWidgets import (QComboBox, QDateEdit, QDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, 
                             QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QTabWidget, QTimeEdit, 
                             QVBoxLayout, QWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QFont, QImage, QPixmap
from services.attendance_service import AttendanceService
from services.leave_service import LeaveService
from services.face_service import FaceService
from models import Employee
from database import get_db_session
from config import Config
from datetime import date
import cv2

class EmployeeTerminal(QWidget):
    def __init__(self):
        super().__init__()
        
        # Camera & Face state
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.known_encodings = []
        self.known_emp_ids = []
        self.frame_count = 0
        self.last_recognized_name = ""
        self.last_recognized_code = ""
        
        # Auto-action state
        self.current_recognizing_id = None
        self.recognition_start_time = None
        self.last_seen_time = None
        self.recent_actions = {} # emp_id -> QTime
        
        config = Config.load_config()
        self.auto_clock_delay = config.get("face_recognition", {}).get("auto_clock_delay_seconds", 3)
        
        # Preload faces
        try:
            session = get_db_session()
            self.known_encodings, self.known_emp_ids = FaceService.load_known_faces(session)
            session.close()
        except Exception as e:
            print(f"Error loading faces on terminal boot: {e}")
            
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)
        
        # Left Side (Camera Container)
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
        
        cam_title = QLabel("Face Recognition Attendance")
        cam_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cam_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        cam_title.setStyleSheet("border: none; margin-bottom: 10px;")
        camera_layout.addWidget(cam_title)
        
        self.video_label = QLabel("Camera Offline")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(400, 300)
        self.video_label.setStyleSheet("background-color: #111; color: #fff; font-size: 18px; border-radius: 8px;")
        
        video_wrap = QHBoxLayout()
        video_wrap.addWidget(self.video_label)
        camera_layout.addLayout(video_wrap)
        
        self.lbl_face_status = QLabel("Turn on camera for face detection.")
        self.lbl_face_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_face_status.setStyleSheet("color: #666; font-size: 14px; font-weight: bold; border: none; margin-top: 10px;")
        camera_layout.addWidget(self.lbl_face_status)
        
        # Camera Toggle Button
        self.btn_toggle_cam = QPushButton("Turn On Camera")
        self.btn_toggle_cam.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; padding: 10px 20px; 
                font-weight: bold; font-size: 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.btn_toggle_cam.clicked.connect(self.toggle_camera)
        
        btn_wrap = QHBoxLayout()
        btn_wrap.addStretch()
        btn_wrap.addWidget(self.btn_toggle_cam)
        btn_wrap.addStretch()
        camera_layout.addLayout(btn_wrap)
        
        camera_layout.addStretch()
        main_layout.addWidget(camera_container, stretch=1)
        
        # Right Side (Keypad Container)
        keypad_container = QFrame()
        keypad_container.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        layout = QVBoxLayout(keypad_container)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Terminal Login")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("border: none; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Display
        # Input Container
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)

        # Display
        self.code_display = QLineEdit()
        self.code_display.setPlaceholderText("Enter Attendance Code or Employee ID")
        self.code_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_display.setFont(QFont("Arial", 24))
        self.code_display.setEchoMode(QLineEdit.EchoMode.Password)
        self.code_display.setReadOnly(False) # Allow keyboard input
        self.code_display.setStyleSheet("border: none; padding: 10px; background: transparent;")
        
        input_layout.addWidget(self.code_display)
        
        # Toggle Button
        self.toggle_btn = QPushButton("👁")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedWidth(60) 
        self.toggle_btn.setFont(QFont("Arial", 20))
        self.toggle_btn.setToolTip("Show/Hide Password")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #777777;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                padding-right: 10px;
            }
            QPushButton:hover {
                color: #333333;
                background-color: #f0f0f0;
            }
        """)
        
        def toggle_password():
            if self.code_display.echoMode() == QLineEdit.EchoMode.Password:
                self.code_display.setEchoMode(QLineEdit.EchoMode.Normal)
                self.toggle_btn.setText("🔒")
            else:
                self.code_display.setEchoMode(QLineEdit.EchoMode.Password)
                self.toggle_btn.setText("👁")
                
        self.toggle_btn.clicked.connect(toggle_password)
        input_layout.addWidget(self.toggle_btn)
        
        layout.addWidget(input_container)
        
        # Keypad
        grid_layout = QGridLayout()
        buttons = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2),
            ('Clear', 3, 0), ('0', 3, 1), ('X', 3, 2)
        ]
        
        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 14))
            btn.setFixedSize(70, 50)
            btn.setStyleSheet("""
                QPushButton { border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9; }
                QPushButton:hover { background-color: #eeeeee; }
                QPushButton:pressed { background-color: #dddddd; }
            """)
            btn.clicked.connect(lambda checked, t=text: self.on_keypad_click(t))
            grid_layout.addWidget(btn, row, col)
            
        layout.addLayout(grid_layout)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        
        self.btn_in = QPushButton("Clock IN")
        self.btn_in.setStyleSheet("background-color: #4CAF50; color: white; padding: 15px; font-size: 14px;")
        self.btn_in.clicked.connect(self.action_clock_in)
        
        self.btn_out = QPushButton("Clock OUT")
        self.btn_out.setStyleSheet("background-color: #f44336; color: white; padding: 15px; font-size: 14px;")
        self.btn_out.clicked.connect(self.action_clock_out)
        
        action_layout.addWidget(self.btn_in)
        action_layout.addWidget(self.btn_out)
        layout.addLayout(action_layout)
        
        # Short Leave Button
        self.btn_leave = QPushButton("Manage Leave")
        self.btn_leave.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-size: 12px;")
        self.btn_leave.clicked.connect(self.open_leave_management)
        layout.addWidget(self.btn_leave)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: blue; font-weight: bold; border: none;")
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        main_layout.addWidget(keypad_container, stretch=1)
        
        self.is_camera_running = False
        
    def toggle_camera(self):
        if not self.is_camera_running:
            self.start_camera()
        else:
            self.stop_camera()
            
    def stop_camera(self):
        self.timer.stop()
        if self.camera:
            self.camera.release()
            self.camera = None
        self.is_camera_running = False
        self.video_label.clear()
        self.video_label.setText("Camera Offline")
        self.btn_toggle_cam.setText("Turn On Camera")
        self.btn_toggle_cam.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; padding: 10px 20px; 
                font-weight: bold; font-size: 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.lbl_face_status.setText("Turn on camera for face detection.")
        
    def start_camera(self):
        self.camera = cv2.VideoCapture(0)
        if self.camera.isOpened():
            self.is_camera_running = True
            self.btn_toggle_cam.setText("Turn Off Camera")
            self.btn_toggle_cam.setStyleSheet("""
                QPushButton {
                    background-color: #f44336; color: white; padding: 10px 20px; 
                    font-weight: bold; font-size: 14px; border-radius: 4px;
                }
                QPushButton:hover { background-color: #d32f2f; }
            """)
            self.lbl_face_status.setText("Scanning for faces...")
            self.timer.start(30)
        else:
            QMessageBox.warning(self, "Camera Error", "Could not access webcam.")
            
    def hideEvent(self, event):
        # Stop camera if terminal goes invisible (e.g. login to admin)
        self.stop_camera()
        super().hideEvent(event)
        
    def showEvent(self, event):
        # Only reload encodings, user must manually turn on camera
        try:
            session = get_db_session()
            self.known_encodings, self.known_emp_ids = FaceService.load_known_faces(session)
            session.close()
        except:
            pass
        super().showEvent(event)

    def update_frame(self):
        if not self.camera:
            return
            
        ret, frame = self.camera.read()
        if not ret:
            return
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 16x speedup by scaling down for face detection
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
        
        # Face Recognition every 5 frames
        self.frame_count += 1
        if self.frame_count % 5 == 0:
            detected_ids = FaceService.match_face(small_frame, self.known_encodings, self.known_emp_ids, tolerance=0.5)
            
            curr_time = QTime.currentTime()
            
            if detected_ids:
                emp_id = detected_ids[0] # Just take first recognized
                self.last_seen_time = curr_time
                
                # Check cooldown
                if emp_id in self.recent_actions:
                    if self.recent_actions[emp_id].secsTo(curr_time) < 60:
                        self.lbl_face_status.setText("Action completed. Please step away.")
                        self.lbl_face_status.setStyleSheet("color: #FF9800; font-size: 16px; font-weight: bold; margin-top: 10px;")
                        self.draw_frame(rgb_frame)
                        return
                        
                if self.current_recognizing_id != emp_id:
                    self.current_recognizing_id = emp_id
                    self.recognition_start_time = curr_time
                    
                    # Fetch name and code immediately upon spotting
                    session = get_db_session()
                    emp = session.query(Employee).get(emp_id)
                    if emp:
                        self.last_recognized_name = emp.full_name
                        self.last_recognized_code = emp.attendance_code
                        if self.code_display.text() != self.last_recognized_code:
                            self.code_display.setText(self.last_recognized_code)
                    session.close()
                else:
                    if self.recognition_start_time is not None:
                        elapsed = self.recognition_start_time.secsTo(curr_time)
                        if elapsed >= self.auto_clock_delay:
                            # TRIGGER AUTO CLOCK!
                            self.auto_clock_action(emp_id)
                            self.current_recognizing_id = None
                            self.recognition_start_time = None
                        else:
                            self.lbl_face_status.setText(f"Hold still... {self.auto_clock_delay - elapsed}s")
                            self.lbl_face_status.setStyleSheet("color: #2196F3; font-size: 18px; font-weight: bold; margin-top: 10px;")
            else:
                # If lost for more than 1 second, reset
                if self.last_seen_time is not None and self.last_seen_time.secsTo(curr_time) > 1:
                    self.current_recognizing_id = None
                    self.recognition_start_time = None
                    self.last_recognized_name = ""
                    self.lbl_face_status.setText("Scanning for faces...")
                    self.lbl_face_status.setStyleSheet("color: #666; font-size: 14px; font-weight: bold; margin-top: 10px;")

        self.draw_frame(rgb_frame)

    def draw_frame(self, rgb_frame):
        # Draw frame (no text overlays as requested)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.width(), self.video_label.height(), Qt.AspectRatioMode.KeepAspectRatio))

    def auto_clock_action(self, emp_id):
        session = get_db_session()
        emp = session.query(Employee).get(emp_id)
        if not emp: return
        
        code = emp.attendance_code
        
        # Try clock IN
        result = AttendanceService.clock_in(session, code)
        if not result['success'] and "Already Clocked In" in result['message']:
            # They must be trying to clock out!
            result = AttendanceService.clock_out(session, code)
            
        self.handle_result(result)
        self.recent_actions[emp_id] = QTime.currentTime()
        self.code_display.clear()
        self.lbl_face_status.setText("Success! Stepping away...")
        self.lbl_face_status.setStyleSheet("color: green; font-size: 18px; font-weight: bold;")

    def on_keypad_click(self, text):
        current = self.code_display.text()
        if text == 'Clear':
            self.code_display.clear()
        elif text == 'X':
            self.code_display.setText(current[:-1])
        else:
            self.code_display.setText(current + text)
                
    def get_code(self):
        code = self.code_display.text().strip()
        if not code:
            self.status_label.setText("Please enter an Attendance Code or Employee ID")
            return None
        return code
        
    def action_clock_in(self):
        code = self.get_code()
        if not code: return
        
        session = get_db_session()
        result = AttendanceService.clock_in(session, code)
        self.handle_result(result)
        
    def action_clock_out(self):
        code = self.get_code()
        if not code: return
        
        session = get_db_session()
        result = AttendanceService.clock_out(session, code)
        self.handle_result(result)
        
    def open_leave_management(self):
        # Authenticate first using the keypad display
        code = self.get_code()
        if not code: return
        
        session = get_db_session()
        employee = session.query(Employee).filter_by(attendance_code=code).first()
        if not employee and code.isdigit():
            employee = session.query(Employee).filter_by(id=int(code)).first()
        if not employee:
            self.status_label.setText("Invalid Code / Employee ID")
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            return
            
        from ui.dialogs.leave_request_dialog import LeaveRequestDialog
        dialog = LeaveRequestDialog(self, session, employee)
        if dialog.exec():
            # If dialog accepted (success), define post-action
            self.status_label.setText("Leave request action completed.")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.code_display.clear()
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def handle_result(self, result):
        if result['success']:
            self.status_label.setText(result['message'])
            self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            self.code_display.clear()
            # Clear status after 3 seconds
            QTimer.singleShot(5000, lambda: self.status_label.setText(""))
        else:
            self.status_label.setText(result['message'])
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            QTimer.singleShot(5000, lambda: self.status_label.setText(""))
