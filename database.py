import streamlit as st
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

def get_db_connection():
    db_url = None
    
    # ניסיון 1: בדיקה אם אנחנו בענן (Streamlit Cloud)
    try:
        # הפקודה הזו תיכשל במחשב המקומי וזה בסדר - נדלג ל-except
        if "DATABASE_URL" in st.secrets:
            db_url = st.secrets["DATABASE_URL"]
            # תיקון ל-Supabase
            if db_url and db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
    except FileNotFoundError:
        pass # אנחנו במחשב מקומי, אין קובץ סודות
    except Exception:
        pass 

    # ניסיון 2: אם לא מצאנו בענן, נבדוק במשתני הסביבה של דוקר (Localhost)
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
        
    if not db_url:
        raise ValueError("Could not find DATABASE_URL in secrets or environment variables")
    
    # לולאת חיבור (למקרה שה-DB עולה לאט)
    while True:
        try:
            engine = create_engine(db_url)
            # בדיקת חיבור קצרה
            connection = engine.connect()
            connection.close()
            return engine
        except Exception as e:
            print(f"Waiting for database... Error: {e}")
            time.sleep(2)

engine = get_db_connection()
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)