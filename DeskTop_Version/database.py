from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from config import Config
from services.audit_logger import setup_audit_logging

Base = declarative_base()

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.engine = None
            cls._instance.Session = None
        return cls._instance
        
    def initialize(self):
        Config.ensure_directories()
        import models # Register all models with Base
        db_url = Config.get_db_url()
        
        # If engine already exists, dispose of it before creating a new one
        if self.engine:
            self.engine.dispose()
            
        self.engine = create_engine(db_url, echo=False)
        
        # Create all tables (safe on existing DB)
        Base.metadata.create_all(self.engine)


        # Run incremental migrations for columns added after initial release
        self._migrate()
        
        # Create session factory
        session_factory = sessionmaker(bind=self.engine)
        
        # If Session already exists (scoped), remove it first
        if self.Session:
            self.Session.remove()
            
        self.Session = scoped_session(session_factory)
        
        # Initialize global audit logging
        setup_audit_logging(self.Session)

    def reconnect(self):
        """Disposes current engine and re-initializes from latest config."""
        self.initialize()

    def _migrate(self):
        """Safely add new columns to existing tables (idempotent)."""
        migrations = [
            "ALTER TABLE shifts ADD COLUMN company_id INTEGER REFERENCES companies(id)",
            "ALTER TABLE shifts ADD COLUMN business_area_id INTEGER REFERENCES business_areas(id)",
        ]
        with self.engine.connect() as conn:
            for stmt in migrations:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception:
                    pass  # Column already exists — safe to ignore
        
    def get_session(self):
        if not self.Session:
            self.initialize()
        return self.Session()
        
    def close_session(self, session):
        if session:
            session.close()

# Global database instance
db = Database()

def get_db_session():
    return db.get_session()

