"""
Utility script to reset the database to a completely clean, empty state with 0 records.
"""
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from app.database import engine, Base, DATA_DIR

def reset_database():
    db_path = os.path.join(DATA_DIR, "health_reports.db")
    
    # Drop all tables or remove sqlite file
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database file: {db_path}")
        except Exception as e:
            print(f"Could not remove file directly ({e}), dropping all tables instead...")
            Base.metadata.drop_all(bind=engine)

    # Re-create pristine, empty tables
    Base.metadata.create_all(bind=engine)
    print("Database reset successfully: Created clean, empty tables with 0 records.")

if __name__ == "__main__":
    reset_database()
