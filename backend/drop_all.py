import os
from database import SessionLocal
import models

def drop_all_data():
    db = SessionLocal()
    try:
        print("Cleaning database...")
        db.query(models.Interview).delete()
        db.query(models.Assessment).delete()
        db.query(models.Application).delete()
        db.query(models.Job).delete()
        db.query(models.Company).delete()
        db.query(models.User).delete()
        db.commit()
        print("Done. Database users table is clear!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    drop_all_data()
