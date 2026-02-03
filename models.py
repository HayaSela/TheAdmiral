from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, BigInteger, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Stock(Base):
    """
    DIM TABLE: טבלת המימד של המניות.
    """
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True) 
    
    # --- זהות ופרופיל ---
    shortName = Column(String, nullable=True)
    longName = Column(String, nullable=True)
    quoteType = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    exchange = Column(String, nullable=True)
    
    # --- סיווג ---
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    
    # --- מיקום וקשר ---
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # --- נתונים ארגוניים ---
    fullTimeEmployees = Column(Integer, nullable=True)
    longBusinessSummary = Column(Text, nullable=True)

    # --- קשרים (Relationships) ---
    # אלו השורות הקריטיות שיוצרות את החיבורים לטבלאות האחרות
    
    quotes = relationship("StockQuote", back_populates="stock", cascade="all, delete-orphan")
    
    transactions = relationship("Transaction", back_populates="stock", cascade="all, delete-orphan")
    
    # הקשר לפוזיציה (One-to-One)
    position = relationship("Position", uselist=False, back_populates="stock", cascade="all, delete-orphan")


class StockQuote(Base):
    """
    FACT TABLE: נתונים היסטוריים מ-Yahoo.
    """
    __tablename__ = "stock_quotes"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    
    # מחירים
    currentPrice = Column(Float, nullable=True)
    open = Column(Float, nullable=True)
    previousClose = Column(Float, nullable=True)
    dayHigh = Column(Float, nullable=True)
    dayLow = Column(Float, nullable=True)
    
    # טווחי זמן
    fiftyTwoWeekHigh = Column(Float, nullable=True)
    fiftyTwoWeekLow = Column(Float, nullable=True)
    fiftyTwoWeekChange = Column(Float, nullable=True)
    fiftyDayAverage = Column(Float, nullable=True)
    twoHundredDayAverage = Column(Float, nullable=True)
    
    # שווי ונפח
    marketCap = Column(BigInteger, nullable=True)
    enterpriseValue = Column(BigInteger, nullable=True)
    volume = Column(BigInteger, nullable=True)
    averageVolume = Column(BigInteger, nullable=True)
    
    # מכפילים
    trailingPE = Column(Float, nullable=True)
    forwardPE = Column(Float, nullable=True)
    pegRatio = Column(Float, nullable=True)
    priceToBook = Column(Float, nullable=True)
    profitMargins = Column(Float, nullable=True)
    
    # דיבידנד
    dividendRate = Column(Float, nullable=True)
    dividendYield = Column(Float, nullable=True)
    
    # פיננסי
    totalRevenue = Column(BigInteger, nullable=True)
    revenueGrowth = Column(Float, nullable=True)
    ebitda = Column(BigInteger, nullable=True)
    
    recommendationKey = Column(String, nullable=True)

    # קשר הופכי למניה
    stock = relationship("Stock", back_populates="quotes")


class Transaction(Base):
    """
    טבלת הפעולות: כל קנייה ומכירה נרשמת כאן.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)

    # קשר הופכי למניה
    stock = relationship("Stock", back_populates="transactions")


class Position(Base):
    """
    טבלת הפוזיציות: המצב המחושב.
    """
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), unique=True)
    
    # נתונים מחושבים
    quantity = Column(Float, default=0.0)
    average_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # נתוני שוק
    current_price = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    daily_change = Column(Float, default=0.0)
    daily_change_percent = Column(Float, default=0.0)
    
    notes = Column(Text, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

    # --- התיקון הקריטי ---
    # השורה הזו הייתה חסרה כנראה, או לא תאמה לשם שהוגדר ב-Stock
    stock = relationship("Stock", back_populates="position")