from typing import List, Optional

from ..models import StockSnapshot
from .base import DataProvider


def _latest_value(series) -> Optional[float]:
    """First (most recent) value out of a yfinance cash-flow row, or None
    if the row is missing/empty/NaN."""
    if series is None or len(series) == 0:
        return None
    value = series.iloc[0]
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if value != value else value  # NaN != NaN


class YFinanceProvider(DataProvider):
    """Fetches live fundamentals + cash-flow-statement data via the
    `yfinance` library (unofficial -- calls/scrapes Yahoo Finance, no
    account or API key needed).

    Unlike RobinhoodProvider, this also supplies operating_cash_flow and
    capital_expenditures directly from Yahoo's cash flow statement, so FCF
    and DCF metrics don't require manually copying numbers out of a 10-K.

    Caveats, since this couldn't be verified against live data from this
    environment's sandboxed network:
    - yfinance is unofficial; Yahoo has changed field semantics before, so
      spot-check a result against a stock with a well-known P/E or
      dividend yield the first time you use this.
    - `dividend_yield` is assumed to already be expressed as a percentage
      (e.g. 2.5 for 2.5%), matching the convention used elsewhere in this
      project (CSVProvider, RobinhoodProvider). If your installed
      yfinance version returns a fraction (e.g. 0.025) instead, multiply
      by 100 here.
    - Not every ticker has a "Operating Cash Flow" / "Capital Expenditure"
      row in its cash flow statement (e.g. some ETFs, foreign filers) --
      those fields are left as None rather than guessed.
    """

    def __init__(self, yfinance_module=None):
        if yfinance_module is not None:
            self._yf = yfinance_module
            return
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError(
                "yfinance is required for the yfinance provider. Install it with: pip install yfinance"
            ) from exc
        self._yf = yf

    def get_snapshots(self, symbols: Optional[List[str]]) -> List[StockSnapshot]:
        if not symbols:
            raise ValueError("YFinanceProvider requires an explicit list of symbols.")

        snapshots = []
        for symbol in symbols:
            ticker = self._yf.Ticker(symbol)
            info = ticker.info or {}
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
            if not price:
                continue

            operating_cash_flow, capital_expenditures = self._cash_flow_inputs(ticker)

            snapshots.append(
                StockSnapshot(
                    symbol=symbol.upper(),
                    price=float(price),
                    pe_ratio=info.get("trailingPE"),
                    pb_ratio=info.get("priceToBook"),
                    dividend_yield=info.get("dividendYield"),
                    market_cap=info.get("marketCap"),
                    high_52_weeks=info.get("fiftyTwoWeekHigh"),
                    low_52_weeks=info.get("fiftyTwoWeekLow"),
                    sector=info.get("sector"),
                    industry=info.get("industry"),
                    operating_cash_flow=operating_cash_flow,
                    capital_expenditures=capital_expenditures,
                )
            )
        return snapshots

    @staticmethod
    def _cash_flow_inputs(ticker):
        try:
            cash_flow = ticker.cashflow
        except Exception:
            return None, None
        if cash_flow is None or cash_flow.empty:
            return None, None

        operating_cash_flow = (
            _latest_value(cash_flow.loc["Operating Cash Flow"]) if "Operating Cash Flow" in cash_flow.index else None
        )
        raw_capex = (
            _latest_value(cash_flow.loc["Capital Expenditure"]) if "Capital Expenditure" in cash_flow.index else None
        )
        # Yahoo reports capex as a negative outflow; the rest of this project
        # (metrics.free_cash_flow, the CSV format) treats it as a positive
        # magnitude to subtract, so normalize the sign here.
        capital_expenditures = abs(raw_capex) if raw_capex is not None else None
        return operating_cash_flow, capital_expenditures
