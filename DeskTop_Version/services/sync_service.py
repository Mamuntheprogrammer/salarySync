import os
from datetime import datetime
from config import Config
from database import get_db_session, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class SyncService:
    def __init__(self):
        pass
        
    def test_remote_connection(self, connection_string):
        """
        Tests connection to remote DB.
        """
        if not connection_string:
            return False, "Empty connection string"
            
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                pass
            return True, "Connection Successful"
        except Exception as e:
            return False, f"Connection Failed: {e}"

    def push_to_remote_db(self, connection_string, reset=False):
        """
        Pushes all local data to remote DB.
        If reset is True, drops all tables on remote first.
        """
        if not connection_string:
            return False, "No connection string provided"
            
        try:
            remote_engine = create_engine(connection_string)
            
            # Local Session
            local_session = get_db_session()
            
            # If reset, drop all tables on remote
            if reset:
                Base.metadata.drop_all(remote_engine)
                
            # Ensure tables exist
            Base.metadata.create_all(remote_engine)
            
            from sqlalchemy.orm import sessionmaker
            RemoteSession = sessionmaker(bind=remote_engine)
            remote_session = RemoteSession()
            
            # Function to copy table data
            def copy_table(model_class):
                # Clear remote table if reset was already done via drop_all
                # If reset is False, we just upsert/insert
                
                records = local_session.query(model_class).all()
                for rec in records:
                    data = {c.name: getattr(rec, c.name) for c in rec.__table__.columns}
                    
                    # Try to get by ID
                    existing = remote_session.query(model_class).get(data['id'])
                    if existing:
                        for k, v in data.items():
                            setattr(existing, k, v)
                    else:
                        new_obj = model_class(**data)
                        remote_session.add(new_obj)
            
            # Models: Company, BusinessArea, Holiday, Shift, Designation, DesignationSubcategory, Employee, Attendance, ShortLeave, LeaveRequest, AdminUser, PayrollConfig
            from models import Company, BusinessArea, HolidayCalendar, WeeklyHoliday, LeaveQuota, Shift, Designation, DesignationSubcategory, Employee, Attendance, ShortLeave, LeaveRequest, AdminUser, PayrollConfig

            # Process in dependency order
            copy_table(Company)
            copy_table(BusinessArea)
            copy_table(HolidayCalendar)
            copy_table(WeeklyHoliday)
            copy_table(LeaveQuota)
            copy_table(Shift)
            copy_table(Designation)
            copy_table(DesignationSubcategory)
            
            remote_session.flush() 
            
            copy_table(Employee)
            copy_table(AdminUser)
            copy_table(PayrollConfig)
            
            remote_session.flush()
            
            copy_table(Attendance)
            copy_table(ShortLeave)
            copy_table(LeaveRequest)
            
            remote_session.commit()
            local_session.close()
            remote_session.close()
            
            # Update Config
            config = Config.load_config()
            if "remote_db" not in config:
                config["remote_db"] = {}
                
            config["remote_db"]["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            Config.save_config(config)
            
            return True, "Data pushed to remote database"
            
        except Exception as e:
            return False, f"Remote Push Failed: {e}"

    def pull_from_remote_db(self, connection_string):
        """
        Pulls data from Remote DB and replaces Local DB content (Backup Logic).
        This essentially does: Remote -> Local.
        WARNING: This overwrites local changes if IDs conflict. 
        But since this is a "Restore/Backup" feature, replacing is expected behavior?
        Actually for "Backup to Local", we usually mean "Dump remote content to local file".
        
        The requirement is "backup online to sqllite db".
        So we iterate Remote -> Insert into Local.
        """
        if not connection_string:
            return False, "No connection string provided"
            
        try:
            remote_engine = create_engine(connection_string)
            RemoteSession = sessionmaker(bind=remote_engine)
            remote_session = RemoteSession()
            
            local_session = get_db_session()
            
            # Helper to copy from remote to local
            def pull_table(model_class):
                # We can't easily drop all local tables because of lock?
                # Best is to upsert.
                
                records = remote_session.query(model_class).all()
                count = 0
                for rec in records:
                    data = {c.name: getattr(rec, c.name) for c in rec.__table__.columns}
                    
                    existing = local_session.query(model_class).get(data['id'])
                    if existing:
                        for k, v in data.items():
                            setattr(existing, k, v)
                    else:
                        new_obj = model_class(**data)
                        local_session.add(new_obj)
                    count += 1
                return count

            from models import Company, BusinessArea, HolidayCalendar, WeeklyHoliday, LeaveQuota, Shift, Designation, DesignationSubcategory, Employee, Attendance, ShortLeave, LeaveRequest, AdminUser, PayrollConfig
            
            # Order matters
            pull_table(Company)
            pull_table(BusinessArea)
            pull_table(HolidayCalendar)
            pull_table(WeeklyHoliday)
            pull_table(LeaveQuota)
            pull_table(Shift)
            pull_table(Designation)
            pull_table(DesignationSubcategory)
            
            local_session.flush()
            
            pull_table(Employee)
            pull_table(AdminUser)
            pull_table(PayrollConfig)
            
            local_session.flush()
            
            pull_table(Attendance)
            pull_table(ShortLeave)
            pull_table(LeaveRequest)
            
            local_session.commit()
            remote_session.close()
            local_session.close()
            
            return True, "Remote data backed up to Local DB"
            
        except Exception as e:
            return False, f"Backup Failed: {e}"
