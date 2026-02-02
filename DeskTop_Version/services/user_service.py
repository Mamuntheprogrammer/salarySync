import bcrypt
from sqlalchemy.orm import Session
from models import AdminUser
from database import get_db_session

class UserService:
    @staticmethod
    def create_user(session: Session, username, password, role="user", employee_id=None):
        if session.query(AdminUser).filter_by(username=username).first():
            raise ValueError("Username already exists")
            
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = AdminUser(
            username=username,
            password_hash=hashed.decode('utf-8'),
            role=role,
            employee_id=employee_id
        )
        session.add(user)
        session.commit()
        return user

    @staticmethod
    def authenticate(session: Session, username, password):
        user = session.query(AdminUser).filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return user
        return None

    @staticmethod
    def reset_password(session: Session, user_id, new_password):
        user = session.query(AdminUser).get(user_id)
        if not user:
            raise ValueError("User not found")
            
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.password_hash = hashed.decode('utf-8')
        session.commit()
        return True

    @staticmethod
    def delete_user(session: Session, user_id):
        user = session.query(AdminUser).get(user_id)
        if user:
            session.delete(user)
            session.commit()
            return True
        return False

    @staticmethod
    def get_all_users(session: Session):
        return session.query(AdminUser).all()
