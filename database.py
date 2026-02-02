import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# המתנה שה-DB יעלה (רק בהפעלה ראשונית)
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set")
    
    # ניסיון התחברות בלולאה (למנוע קריסה בהתחלה)
    while True:
        try:
            engine = create_engine(db_url)
            connection = engine.connect()
            connection.close()
            print("Successfully connected to the database!")
            return engine
        except Exception as e:
            print("Database not ready yet, waiting 2 seconds...")
            time.sleep(2)

# יצירת המנוע
engine = get_db_connection()

# הבסיס לכל הטבלאות שניצור בהמשך
Base = declarative_base()

# יצירת סשן (החיבור בפועל לשימוש בקוד)
SessionLocal = sessionmaker(bind=engine)