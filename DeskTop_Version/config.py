import os
import json
from pathlib import Path

class Config:
    APP_NAME = "AttenSync HRMS"
    VERSION = "1.0.0"
    
    # Default Paths
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    BACKUP_DIR = BASE_DIR / "backups"
    CONFIG_FILE = DATA_DIR / "config.json"
    
    # Default Configuration
    DEFAULT_CONFIG = {
        "company_name": "My Company",
        "time_format": "24h", # 12h or 24h
        "db_path": str(DATA_DIR / "attensync_v3.db"),
        "theme": "Dark",
        "backup_frequency": "daily",
        "backup_location": str(BACKUP_DIR),
        "backup": {
            "enabled": True,
            "frequency": "daily", # daily, weekly
            "location": str(BACKUP_DIR),
            "last_backup_date": None 
        },
        "online_mode": False, # If True, connects directly to remote_db
        "cloud_sync": {
            # Kept generic if we add other syncs later, but for now simplified
            "enabled": True, 
            "last_sync": None
        },
        "remote_db": {
            "connection_string": "", # sqlalchemy URI
            "last_backup": None
        },
        "face_recognition": {
            "auto_clock_delay_seconds": 3
        }
    }
    
    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
    @classmethod
    def load_config(cls):
        cls.ensure_directories()
        if not cls.CONFIG_FILE.exists():
            cls.save_config(cls.DEFAULT_CONFIG)
            return cls.DEFAULT_CONFIG
            
        try:
            with open(cls.CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return cls.DEFAULT_CONFIG
            
    @classmethod
    def save_config(cls, config_data):
        cls.ensure_directories()
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
            
    @classmethod
    def get_db_url(cls):
        config = cls.load_config()
        
        # Check Online Mode
        if config.get("online_mode"):
            remote_uri = config.get("remote_db", {}).get("connection_string")
            if remote_uri:
                return remote_uri
                
        # Default Local
        db_path = config.get("db_path", str(cls.DATA_DIR / "attensync.db"))
        return f"sqlite:///{db_path}"

    @classmethod
    def get_time_fmt(cls):
        """Returns Python strftime format string"""
        config = cls.load_config()
        return "%I:%M %p" if config.get("time_format") == "12h" else "%H:%M"

    @classmethod
    def get_qt_time_fmt(cls):
        """Returns Qt time format string"""
        config = cls.load_config()
        return "hh:mm AP" if config.get("time_format") == "12h" else "HH:mm"
