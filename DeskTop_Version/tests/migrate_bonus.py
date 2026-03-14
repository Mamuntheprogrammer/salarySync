from database import db
from models import Bonus

def migrate():
    print("Initializing database...")
    db.initialize()
    print("Creating 'bonuses' table in the database...")
    Bonus.__table__.create(db.engine, checkfirst=True)
    print("Migration successful! 'bonuses' table created.")

if __name__ == "__main__":
    migrate()
