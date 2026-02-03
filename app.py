import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from portfolio_engine import PortfolioEngine
# --- התיקון הקריטי: ייבוא כל רכיבי הזמן והמימון ---
import yfinance as yf
from datetime import datetime, date, timedelta 
import market_data 
# --------------------------------------------------

# --- יצירת טבלאות (למקרה שנמחקו) ---
models.Base.metadata.create_all(bind=engine)

# --- הגדרות עמוד ---
st.set_page_config(page_title="The Admiral", layout="wide", page_icon="⚓")

# --- פונקציות עזר ---
def run_full_sync():
    """מריץ את המנוע: חישוב מחדש + משיכת מחירים"""
    with SessionLocal() as db:
        pe = PortfolioEngine(db)
        status = st.empty()
        status.info("⏳ מחשב נתונים מחדש...")
        pe.recalculate_positions()
        status.info("☁️ מושך מחירים מ-Yahoo...")
        pe.refresh_prices()
        status.success("✅ הנתונים מעודכנים!")
        return pe.get_portfolio_summary()

def get_positions_data():
    """שליפת נתוני הפוזיציות המחושבים"""
    with SessionLocal() as db:
        if db.query(models.Stock).count() == 0:
            return pd.DataFrame()

        positions = db.query(models.Position).join(models.Stock).all()
        data = []
        for p in positions:
            data.append({
                "Symbol": p.stock.symbol,
                "Qty": p.quantity,
                "Avg Cost ($)": p.average_cost,
                "Current ($)": p.current_price,
                "Value ($)": p.current_value,
                "Total Cost ($)": p.total_cost,
                "Profit ($)": p.current_value - p.total_cost,
                "Profit (%)": ((p.current_value - p.total_cost) / p.total_cost * 100) if p.total_cost > 0 else 0,
                "Daily Change ($)": p.daily_change,
                "Daily Change (%)": p.daily_change_percent
            })
        return pd.DataFrame(data)

def get_db_stocks():
    """שליפת רשימת מניות למילוי תיבת הבחירה"""
    with SessionLocal() as db:
        try:
            stocks = db.query(models.Stock).all()
            return {s.symbol: s.id for s in stocks}
        except Exception:
            return {}

# --- ממשק משתמש (UI) ---

# סרגל צד
with st.sidebar:
    st.header("פעולות מערכת")
    if st.button("🔄 רענן נתונים (Live)"):
        with st.spinner("מעדכן מול השווקים..."):
            run_full_sync()
            st.rerun()

# כותרת
st.title("⚓ The Admiral")

# חישוב מדדים
try:
    with SessionLocal() as db:
        pe = PortfolioEngine(db)
        summary = pe.get_portfolio_summary()

    # הוספנו עמודה חמישית לכמות המניות
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("שווי תיק כולל", f"${summary['total_value']:,.2f}", f"${summary['daily_change']:,.2f}")
    col2.metric("עלות השקעה", f"${summary['total_invested']:,.2f}")
    col3.metric("רווח/הפסד ($)", f"${summary['total_pnl']:,.2f}")
    col4.metric("תשואה (%)", f"{summary['total_pnl_percent']:.2f}%")
    col5.metric("מניות בתיק", f"{summary.get('positions_count', 0)}")

except Exception as e:
    st.warning("המערכת באתחול. נא לטעון מניות בטאב 'ניהול'.")

st.divider()

# טאבים ראשיים
tab1, tab2, tab3, tab4 = st.tabs(["📊 התיק שלי", "💰 ביצוע פעולה", "🔍 בדיקה חיה", "⚙️ ניהול"])

# --- טאב 1: התיק שלי ---
with tab1:
    try:
        df = get_positions_data()
        if not df.empty:
            st.dataframe(
                df,
                column_config={
                    "Avg Cost ($)": st.column_config.NumberColumn(format="$%.2f"),
                    "Current ($)": st.column_config.NumberColumn(format="$%.2f"),
                    "Value ($)": st.column_config.NumberColumn(format="$%.0f"),
                    "Profit ($)": st.column_config.NumberColumn(format="$%.0f"),
                    "Profit (%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "Daily Change (%)": st.column_config.NumberColumn(format="%.2f%%"),
                },
                use_container_width=True,
                hide_index=True,
                height=400
            )
        else:
            st.info("התיק ריק. עבור לטאב 'ניהול' להוספת מניות, ואז ל'ביצוע פעולה'.")
    except Exception as e:
        st.error(f"שגיאה בטעינת הנתונים: {e}")

# --- טאב 2: ביצוע פעולה (חכם - משיכת מחיר היסטורי) ---
with tab2:
    st.header("יומן מסחר")
    stock_map = get_db_stocks()
    
    if not stock_map:
        st.warning("אין מניות במערכת. טען מניות בטאב 'ניהול' תחילה.")
    else:
        # --- חלק 1: בחירת נתונים (מחוץ לטופס) ---
        c_sel1, c_sel2 = st.columns(2)
        with c_sel1:
            selected_symbol = st.selectbox("בחר מניה", list(stock_map.keys()))
        with c_sel2:
            trade_date = st.date_input("תאריך העסקה", datetime.today())

        # --- חלק 2: משיכת שער פתיחה היסטורי ---
        suggested_price = 0.0
        price_source_text = "לא נמצא נתון"
        
        if selected_symbol:
            try:
                # שימוש ב-timedelta לחישוב טווח של יום אחד
                end_date = trade_date + timedelta(days=1)
                df_hist = yf.Ticker(selected_symbol).history(start=trade_date, end=end_date)
                
                if not df_hist.empty:
                    suggested_price = float(df_hist.iloc[0]['Open'])
                    price_source_text = f"שער פתיחה לתאריך {trade_date}"
                else:
                    info = yf.Ticker(selected_symbol).info
                    suggested_price = info.get('currentPrice', 0.0)
                    price_source_text = "אין מסחר בתאריך זה (נלקח מחיר אחרון)"
                    
            except Exception as e:
                # במקרה של שגיאה נשארים עם 0 ולא קורסים
                suggested_price = 0.0
                price_source_text = "שגיאה במשיכת נתונים"

        st.info(f"💡 {price_source_text}: **${suggested_price:.2f}**")

        # --- חלק 3: הטופס ---
        with st.form("trade_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**מניה:** {selected_symbol}")
                action = st.selectbox("פעולה", ["BUY", "SELL"])
            with c2:
                qty = st.number_input("כמות", min_value=0.01, step=1.0, value=1.0)
                price = st.number_input("מחיר ביצוע ($)", min_value=0.01, step=0.1, value=suggested_price)
            with c3:
                st.write(f"**תאריך:** {trade_date}")
                fees = st.number_input("עמלה ($)", min_value=0.0, step=0.5)
            
            submit = st.form_submit_button("✅ בצע הוראה")
            
            if submit:
                # בדיקת תקינות למכירה
                is_valid = True
                if action == 'SELL':
                    with SessionLocal() as db:
                        current_pos = db.query(models.Position).filter_by(stock_id=stock_map[selected_symbol]).first()
                        current_qty = current_pos.quantity if current_pos else 0.0
                    
                    if qty > current_qty:
                        st.error(f"⛔ שגיאה: יש לך בתיק רק {current_qty} מניות.")
                        is_valid = False
                
                if is_valid:
                    total = (qty * price) + fees if action == 'BUY' else (qty * price) - fees
                    
                    try:
                        with SessionLocal() as db:
                            tx = models.Transaction(
                                stock_id=stock_map[selected_symbol],
                                date=trade_date,
                                type=action,
                                quantity=qty,
                                price=price,
                                fees=fees,
                                total_amount=total
                            )
                            db.add(tx)
                            db.commit()
                            
                            pe = PortfolioEngine(db)
                            pe.recalculate_positions()
                            
                        st.success(f"בוצע! נרשמה פעולה ב-{trade_date}")
                        # המתנה קצרה כדי לראות את ההודעה
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"שגיאה: {e}")

# --- טאב 3: בדיקה חיה ---
with tab3:
    t = st.text_input("סימול לבדיקה", "NVDA")
    if st.button("בדוק"):
        try:
            d = yf.Ticker(t).history(period="1mo")
            if not d.empty:
                st.line_chart(d['Close'])
            else:
                st.error("לא נמצאו נתונים")
        except:
            st.error("שגיאה במשיכת נתונים")

# --- טאב 4: ניהול ---
with tab4:
    st.header("מערכת ניהול קטלוג")
    
    tickers_input = st.text_area("הכנס רשימת מניות (מופרדות בפסיק)", "AAPL, MSFT, TSLA, GOOGL, NVDA")
    
    if st.button("📥 טען מניות לקטלוג"):
        if not tickers_input.strip():
            st.warning("נא להזין סימול מניה אחד לפחות.")
        else:
            t_list = [x.strip().upper() for x in tickers_input.split(",") if x.strip()]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, tick in enumerate(t_list):
                status_text.text(f"מושך נתונים עבור: {tick}...")
                try:
                    market_data.fetch_and_store_data(tick)
                except Exception as e:
                    st.error(f"שגיאה בטעינת {tick}: {e}")
                
                progress_bar.progress((i + 1) / len(t_list))
            
            status_text.success("✅ המניות נטענו בהצלחה!")
            st.rerun()
            
    st.divider()
    st.subheader("⚠️ אזור סכנה")
    
    if st.button("🔴 מחק את כל הנתונים והתחל מחדש"):
        try:
            with SessionLocal() as db:
                db.query(models.Position).delete()
                db.query(models.Transaction).delete()
                db.commit()
            
            st.success("הנתונים נמחקו בהצלחה! המערכת נקייה.")
            run_full_sync()
            st.rerun()
            
        except Exception as e:
            st.error(f"שגיאה במחיקה: {e}")