import streamlit as st
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

def get_db_connection():
    # 1. בדיקה האם אנחנו בענן (יש סודות)
    if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]
        # תיקון קטן ל-Supabase
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
    # 2. אחרת, אנחנו במחשב המקומי (לוקחים מה-Docker Compose)
    else:
        db_url = os.getenv("DATABASE_URL")
        
    if not db_url:
        raise ValueError("DATABASE_URL is not set")
    
    # ניסיון התחברות (חשוב להפעלה ראשונית של דוקר)
    while True:
        try:
            engine = create_engine(db_url)
            connection = engine.connect()
            connection.close()
            return engine
        except Exception as e:
            print("Waiting for database...", e)
            time.sleep(2)

engine = get_db_connection()
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)