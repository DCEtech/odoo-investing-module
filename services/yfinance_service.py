import yfinance as yf
import logging

_logger = logging.getLogger(__name__)

class YFinanceService:
    
    def get_company_data(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            data = stock.info
            if not data:
                raise ValueError(f"NO data found for ticker: {ticker}")
            return data
        except Exception as e:
            _logger.error("YFinance error for ticker %s: %s", ticker, str(e))
            raise

    def get_current_price(self, ticker):
        try:
            info = yf.Ticker(ticker).info
            return info.get('currentPrice') or info.get('regularMarketPrice') or 0.0
        except Exception as e:
            _logger.error("YFinance price error for %s: %s", ticker, str(e))
            return 0.0
    
    def get_price_history(self, ticker, period="1y"): 
        try: 
            hist = yf.Ticker(ticker).history(period=period)
            if hist.empty:
                raise ValueError(f"No history found for ticker: {ticker}")
            return hist 
        except Exception as e:
            _logger.error("YFinance history error for %s: %s", ticker, str(e))
            raise
    




