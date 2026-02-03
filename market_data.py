import yfinance as yf
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def sanitize_value(val):
    """פונקציית עזר לניקוי נתונים: הופכת 'None' או ערכים ריקים ל-None של פייתון"""
    if pd.isna(val) or val == 'N/A' or val == float('inf'):
        return None
    return val

def fetch_and_store_data(symbol: str):
    """
    פונקציה ראשית: מקבלת סימול, מביאה מידע, ושומרת ב-DB
    """
    print(f"⚓ Fetching data for: {symbol}...")
    
    # 1. משיכת המידע מ-Yahoo
    ticker = yf.Ticker(symbol)
    
    # info מכיל את רוב הנתונים הפיננסיים והתיאוריים
    try:
        info = ticker.info
    except Exception as e:
        print(f"❌ Error fetching data from Yahoo for {symbol}: {e}")
        return

    db: Session = SessionLocal()
    
    try:
        # --- שלב א': טיפול בטבלת המניות (DIM_STOCKS) ---
        # בודקים אם המניה כבר קיימת במערכת
        stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
        
        if not stock:
            print(f"   Creating new stock entry for {symbol}")
            stock = models.Stock(symbol=symbol)
            db.add(stock)
        
        # עדכון שדות תיאוריים (תמיד מעדכנים למקרה שמשהו השתנה)
        stock.shortName = info.get('shortName')
        stock.longName = info.get('longName')
        stock.quoteType = info.get('quoteType')
        stock.currency = info.get('currency')
        stock.exchange = info.get('exchange')
        stock.sector = info.get('sector')
        stock.industry = info.get('industry')
        stock.city = info.get('city')
        stock.country = info.get('country')
        stock.website = info.get('website')
        stock.fullTimeEmployees = info.get('fullTimeEmployees')
        stock.longBusinessSummary = info.get('longBusinessSummary')
        
        # שמירה כדי לקבל את ה-ID של המניה
        db.commit()
        db.refresh(stock)

        # --- שלב ב': הוספת שורה לטבלת הנתונים (FACT_QUOTES) ---
        # יצירת אובייקט ציטוט חדש
        quote = models.StockQuote()
        quote.stock_id = stock.id
        
        # זיהוי זמן הדגימה (Yahoo לפעמים נותן שמות שונים לשדה הזמן)
        # אנחנו מנסים לקחת את זמן השוק האמיתי
        market_time = info.get('regularMarketTime', info.get('preMarketTime'))
        if market_time:
            quote.timestamp = datetime.fromtimestamp(market_time)
        else:
            quote.timestamp = datetime.now()

        # --- מיפוי נתונים (Mapping) ---
        # מחירים
        quote.currentPrice = sanitize_value(info.get('currentPrice'))
        quote.open = sanitize_value(info.get('open'))
        quote.previousClose = sanitize_value(info.get('previousClose'))
        quote.dayHigh = sanitize_value(info.get('dayHigh'))
        quote.dayLow = sanitize_value(info.get('dayLow'))
        
        # טווחים
        quote.fiftyTwoWeekHigh = sanitize_value(info.get('fiftyTwoWeekHigh'))
        quote.fiftyTwoWeekLow = sanitize_value(info.get('fiftyTwoWeekLow'))
        quote.fiftyTwoWeekChange = sanitize_value(info.get('52WeekChange'))
        quote.fiftyDayAverage = sanitize_value(info.get('fiftyDayAverage'))
        quote.twoHundredDayAverage = sanitize_value(info.get('twoHundredDayAverage'))
        
        # שווי ונפח
        quote.marketCap = sanitize_value(info.get('marketCap'))
        quote.enterpriseValue = sanitize_value(info.get('enterpriseValue'))
        quote.volume = sanitize_value(info.get('volume'))
        quote.averageVolume = sanitize_value(info.get('averageVolume'))
        
        # מכפילים
        quote.trailingPE = sanitize_value(info.get('trailingPE'))
        quote.forwardPE = sanitize_value(info.get('forwardPE'))
        quote.pegRatio = sanitize_value(info.get('pegRatio'))
        quote.priceToBook = sanitize_value(info.get('priceToBook'))
        quote.profitMargins = sanitize_value(info.get('profitMargins'))
        
        # דיבידנד
        quote.dividendRate = sanitize_value(info.get('dividendRate'))
        quote.dividendYield = sanitize_value(info.get('dividendYield'))
        
        # פיננסי
        quote.totalRevenue = sanitize_value(info.get('totalRevenue'))
        quote.revenueGrowth = sanitize_value(info.get('revenueGrowth'))
        quote.ebitda = sanitize_value(info.get('ebitda'))
        
        # המלצות
        quote.recommendationKey = info.get('recommendationKey')

        # שמירת הציטוט
        db.add(quote)
        db.commit()
        print(f"✅ Data saved successfully for {symbol}")

    except Exception as e:
        print(f"❌ Database Error for {symbol}: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # רשימת מניות לדוגמה
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]
    
    print("🚀 Starting Data Update...")
    for t in tickers:
        fetch_and_store_data(t)
    print("🏁 Update Complete.")