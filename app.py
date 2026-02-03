import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database import engine, Base
import models
import yfinance as yf
import market_data  # <--- ייבוא הסקריפט שלנו

# --- הגדרות עמוד ---
st.set_page_config(page_title="The Admiral", layout="wide", page_icon="⚓")

# --- פונקציות עזר ---
def get_portfolio_data():
    """שליפת נתונים עדכניים מה-DB"""
    with Session(engine) as session:
        stocks = session.query(models.Stock).all()
        data = []
        for stock in stocks:
            last_quote = session.query(models.StockQuote).\
                filter(models.StockQuote.stock_id == stock.id).\
                order_by(models.StockQuote.timestamp.desc()).\
                first()
            
            if last_quote:
                data.append({
                    "Symbol": stock.symbol,
                    "Name": stock.shortName,
                    "Price ($)": last_quote.currentPrice,
                    "Market Cap": last_quote.marketCap,
                    "Volume": last_quote.volume,
                    "Last Update": last_quote.timestamp
                })
        return pd.DataFrame(data)

# --- ממשק משתמש (UI) ---
st.title("⚓ The Admiral: Stock Command Center")

tab1, tab2, tab3 = st.tabs(["📊 התיק שלי (DB)", "🔍 בדיקה חיה", "⚙️ ניהול"])

with tab1:
    st.subheader("תמונת מצב מהירה (מתוך בסיס הנתונים)")
    if st.button("רענן טבלה"):
        st.rerun()
        
    df = get_portfolio_data()
    if not df.empty:
        st.dataframe(
            df,
            column_config={
                "Price ($)": st.column_config.NumberColumn(format="$%.2f"),
                "Market Cap": st.column_config.NumberColumn(format="$%d"),
                "Last Update": st.column_config.DatetimeColumn(format="D MMM YYYY, HH:mm"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("המסד נתונים ריק. עבור לטאב 'ניהול' כדי לטעון נתונים.")

with tab2:
    st.subheader("בדיקת מניה בזמן אמת")
    ticker = st.text_input("הכנס סימול", "NVDA")
    if st.button("בדוק עכשיו"):
        with st.spinner('מושך נתונים...'):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1mo")
                st.line_chart(hist['Close'])
            except Exception:
                st.error("לא נמצא מידע")

# --- השינוי הגדול בטאב 3 ---
with tab3:
    st.header("מנוע טעינת נתונים")
    st.write("כאן ניתן להזריק נתונים ל-DB (גם מקומי וגם בענן).")
    
    # תיבת טקסט להזנת רשימת מניות
    default_tickers = "AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA"
    tickers_input = st.text_area("הכנס רשימת מניות (מופרדות בפסיק)", default_tickers)
    
    if st.button("🚀 הפעל סנכרון Yahoo Finance"):
        # המרת המחרוזת לרשימה נקייה
        tickers_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(tickers_list):
            status_text.text(f"מעבד נתונים עבור: {ticker}...")
            # קריאה לפונקציה מהקובץ market_data.py
            market_data.fetch_and_store_data(ticker)
            progress_bar.progress((i + 1) / len(tickers_list))
            
        status_text.success("✅ הסנכרון הסתיים בהצלחה! הנתונים נשמרו ב-DB.")
        st.balloons()