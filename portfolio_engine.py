import yfinance as yf
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import models
from database import SessionLocal

class PortfolioEngine:
    
    def __init__(self, db: Session):
        self.db = db

    def recalculate_positions(self):
        """
        משחזר את ההיסטוריה: עובר על כל העסקאות ומחשב כמות וממוצע.
        """
        print("🔄 Engine: Recalculating all positions...")
        
        # 1. שליפת כל המניות
        stocks = self.db.query(models.Stock).all()
        
        for stock in stocks:
            # שליפת עסקאות למניה זו, ממוינות מהישן לחדש
            transactions = self.db.query(models.Transaction)\
                .filter(models.Transaction.stock_id == stock.id)\
                .order_by(models.Transaction.date.asc())\
                .all()
            
            if not transactions:
                self._delete_position(stock.id)
                continue

            # --- לוגיקת החישוב (זהה ל-Dart) ---
            total_quantity = 0.0
            total_cost = 0.0
            
            for tx in transactions:
                if tx.type == 'BUY':
                    total_quantity += tx.quantity
                    total_cost += tx.total_amount 
                    
                elif tx.type == 'SELL':
                    if total_quantity > 0:
                        avg_cost = total_cost / total_quantity
                        total_quantity -= tx.quantity
                        total_cost = total_quantity * avg_cost
                    else:
                        total_quantity = 0
                        total_cost = 0

            # --- שמירה ל-DB ---
            if total_quantity > 0.0001: 
                avg_cost = total_cost / total_quantity
                self._update_position_record(stock, total_quantity, avg_cost, total_cost)
            else:
                self._delete_position(stock.id)

    def _update_position_record(self, stock, quantity, avg_cost, total_cost):
        """עדכון או יצירת שורה בטבלת Positions"""
        position = self.db.query(models.Position).filter_by(stock_id=stock.id).first()
        
        if not position:
            position = models.Position(stock_id=stock.id)
            self.db.add(position)
        
        position.quantity = quantity
        position.average_cost = avg_cost
        position.total_cost = total_cost
        
        if position.current_price:
            position.current_value = quantity * position.current_price
            
        position.last_updated = datetime.now()
        self.db.commit()

    def _delete_position(self, stock_id):
        position = self.db.query(models.Position).filter_by(stock_id=stock_id).first()
        if position:
            self.db.delete(position)
            self.db.commit()

    def refresh_prices(self):
        """משיכת מחירים מ-Yahoo ועדכון השווי"""
        print("☁️ Engine: Refreshing market prices...")
        positions = self.db.query(models.Position).all()
        
        if not positions:
            print("No positions to update.")
            return

        tickers_map = {p.stock.symbol: p for p in positions}
        tickers_list = list(tickers_map.keys())
        
        try:
            tickers_str = " ".join(tickers_list)
            data = yf.Tickers(tickers_str)
            
            for symbol, position in tickers_map.items():
                try:
                    info = data.tickers[symbol].info
                    current_price = info.get('currentPrice', info.get('regularMarketPrice'))
                    previous_close = info.get('previousClose')
                    
                    if current_price and previous_close:
                        change = current_price - previous_close
                        change_pct = (change / previous_close) * 100
                        
                        position.current_price = current_price
                        position.current_value = position.quantity * current_price
                        position.daily_change = change * position.quantity
                        position.daily_change_percent = change_pct
                        position.last_updated = datetime.now()
                        
                except Exception as e:
                    print(f"Error updating {symbol}: {e}")
            
            self.db.commit()
            print("✅ Prices updated.")
            
        except Exception as e:
            print(f"❌ Batch price fetch failed: {e}")

    def get_portfolio_summary(self):
        """חישוב סיכומים לדשבורד"""
        positions = self.db.query(models.Position).all()
        
        total_market_value = sum(p.current_value for p in positions)
        total_cost_basis = sum(p.total_cost for p in positions)
        
        total_pnl = total_market_value - total_cost_basis
        total_pnl_percent = (total_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        daily_change_amount = sum(p.daily_change for p in positions)
        
        return {
            "total_value": total_market_value,
            "total_invested": total_cost_basis,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "daily_change": daily_change_amount
        }

# --- בדיקה מהירה ---
if __name__ == "__main__":
    db = SessionLocal()
    engine = PortfolioEngine(db)
    
    engine.recalculate_positions()
    engine.refresh_prices()
    
    summary = engine.get_portfolio_summary()
    print("-" * 30)
    print(f"💰 Portfolio Value: ${summary['total_value']:,.2f}")
    print(f"📉 Total Cost:      ${summary['total_invested']:,.2f}")
    print(f"🚀 Total Profit:    ${summary['total_pnl']:,.2f}")
    print("-" * 30)
    db.close()