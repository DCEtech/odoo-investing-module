import logging

_logger = logging.getLogger(__name__)

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - depends on the server environment
    # Declared in external_dependencies; guarded so a missing library does not
    # prevent the whole registry from loading (e.g. in CI or on a fresh server).
    yf = None
    _logger.warning("The 'yfinance' library is not installed; price sync disabled.")


class YFinanceService:
    @staticmethod
    def _client():
        if yf is None:
            raise RuntimeError("The 'yfinance' Python library is not installed.")
        return yf

    def get_company_data(self, ticker: str) -> dict:
        try:
            data = self._client().Ticker(ticker).info
            if not data:
                raise ValueError(f"No data found for ticker: {ticker}")
            return data
        except Exception as e:
            _logger.error("YFinance error for ticker %s: %s", ticker, e)
            raise

    def get_current_price(self, ticker: str) -> float:
        try:
            info = self._client().Ticker(ticker).info
            return info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        except Exception as e:
            _logger.error("YFinance price error for %s: %s", ticker, e)
            return 0.0

    def get_price_history(self, ticker: str, period: str = "1y"):
        try:
            hist = self._client().Ticker(ticker).history(period=period)
            if hist.empty:
                raise ValueError(f"No history found for ticker: {ticker}")
            return hist
        except Exception as e:
            _logger.error("YFinance history error for %s: %s", ticker, e)
            raise
