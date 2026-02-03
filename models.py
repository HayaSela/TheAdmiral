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

    # קשר לטבלת הנתונים
    quotes = relationship("StockQuote", back_populates="stock", cascade="all, delete-orphan")


class StockQuote(Base):
    """
    FACT TABLE: טבלת העובדות.
    """
    __tablename__ = "stock_quotes"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    
    # --- השינוי שביקשת ---
    # שדה זה יחזיק את ה-Index של Yahoo (תאריך ושעת המסחר המקורית)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    
    # --- מחירים ---
    currentPrice = Column(Float, nullable=True)
    open = Column(Float, nullable=True)
    previousClose = Column(Float, nullable=True)
    dayHigh = Column(Float, nullable=True)
    dayLow = Column(Float, nullable=True)
    
    # --- טווחי זמן ---
    fiftyTwoWeekHigh = Column(Float, nullable=True)
    fiftyTwoWeekLow = Column(Float, nullable=True)
    fiftyTwoWeekChange = Column(Float, nullable=True)
    fiftyDayAverage = Column(Float, nullable=True)
    twoHundredDayAverage = Column(Float, nullable=True)
    
    # --- שווי ונפח ---
    marketCap = Column(BigInteger, nullable=True)
    enterpriseValue = Column(BigInteger, nullable=True)
    volume = Column(BigInteger, nullable=True)
    averageVolume = Column(BigInteger, nullable=True)
    
    # --- מכפילים ורווחיות ---
    trailingPE = Column(Float, nullable=True)
    forwardPE = Column(Float, nullable=True)
    pegRatio = Column(Float, nullable=True)
    priceToBook = Column(Float, nullable=True)
    profitMargins = Column(Float, nullable=True)
    
    # --- דיבידנד ---
    dividendRate = Column(Float, nullable=True)
    dividendYield = Column(Float, nullable=True)
    
    # --- פיננסי ---
    totalRevenue = Column(BigInteger, nullable=True)
    revenueGrowth = Column(Float, nullable=True)
    ebitda = Column(BigInteger, nullable=True)
    
    # --- המלצות ---
    recommendationKey = Column(String, nullable=True)

    stock = relationship("Stock", back_populates="quotes")