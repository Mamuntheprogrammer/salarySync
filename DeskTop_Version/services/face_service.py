import os
import cv2
import numpy as np
import face_recognition
from pathlib import Path
from config import Config
from models import Employee

class FaceService:
    ENCODINGS_DIR = Config.DATA_DIR / "encodings"
    
    @classmethod
    def ensure_dir(cls):
        cls.ENCODINGS_DIR.mkdir(parents=True, exist_ok=True)
        
    @classmethod
    def save_encoding(cls, session, employee, rgb_frame):
        """
        Detects a face in the frame, extracts the encoding, and saves it to a file.
        Updates the employee record in the DB with the file path.
        Returns (success_boolean, message)
        """
        cls.ensure_dir()
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            return False, "No face detected in the frame. Please look into the camera."
        if len(face_locations) > 1:
            return False, "Multiple faces detected. Please ensure only the employee is visible."
            
        # Get encoding
        encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if not encodings:
            return False, "Could not generate face encoding. Try better lighting."
            
        encoding = encodings[0]
        
        # Save to disk as numpy array
        filename = f"emp_{employee.id}_encoding.npy"
        filepath = cls.ENCODINGS_DIR / filename
        np.save(str(filepath), encoding)
        
        # Update Database
        employee.face_encoding_path = str(filepath)
        session.commit()
        
        return True, "Face registered successfully."

    @classmethod
    def delete_encoding(cls, session, employee):
        """
        Removes the face encoding file and clears the database record.
        """
        if employee.face_encoding_path:
            path = Path(employee.face_encoding_path)
            if path.exists():
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error removing file {path}: {e}")
            employee.face_encoding_path = None
            session.commit()
            return True, "Face data unregistered successfully."
        return False, "This employee has no face data to remove."

    @classmethod
    def load_known_faces(cls, session):
        """
        Returns a list of encodings and a corresponding list of employee IDs.
        Looks for all active employees who have a face encoding registered.
        """
        employees = session.query(Employee).filter(
            Employee.is_active == True, 
            Employee.face_encoding_path != None
        ).all()
        
        known_encodings = []
        known_emp_ids = []
        
        for emp in employees:
            path = Path(emp.face_encoding_path)
            if path.exists():
                try:
                    encoding = np.load(str(path))
                    known_encodings.append(encoding)
                    known_emp_ids.append(emp.id)
                except Exception as e:
                    print(f"Error loading face encoding for Employee {emp.id}: {e}")
                    
        return known_encodings, known_emp_ids

    @classmethod
    def match_face(cls, rgb_frame, known_encodings, known_emp_ids, tolerance=0.5):
        """
        Matches any faces in the current frame to the known encodings.
        Returns a list of employee IDs detected, or an empty list.
        Tolerance 0.5 is strict. 0.6 is default.
        """
        if not known_encodings:
            return []
            
        # Find all faces in the current frame
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            return []
            
        # Get encodings for them
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        detected_emp_ids = []
        
        for encoding in face_encodings:
            # See if the face is a match for the known faces
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=tolerance)
            
            # Use distance to find best match
            face_distances = face_recognition.face_distance(known_encodings, encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    detected_emp_ids.append(known_emp_ids[best_match_index])
                    
        return list(set(detected_emp_ids))
