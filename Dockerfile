FROM python:3.9-slim

WORKDIR /app

# התקנת ספריות
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת שאר הקבצים
COPY . .

# חשיפת הפורט של Streamlit (ברירת מחדל 8501)
EXPOSE 8501

# הפקודה להרצת האתר
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]