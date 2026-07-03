from dataclasses import dataclass
from typing import Optional


@dataclass
class StockSnapshot:
    """A point-in-time snapshot of the data needed to value a stock.

    Most fields mirror what's available from Robinhood's fundamentals +
    quote endpoints, since that's the primary data source. Anything not
    known should be left as None rather than guessed.

    operating_cash_flow and capital_expenditures are the exception: Robinhood's
    fundamentals endpoint has no cash-flow-statement data, so these can only
    be populated manually (e.g. from a 10-K/10-Q) via the CSV provider.
    """

    symbol: str
    price: float
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    market_cap: Optional[float] = None
    high_52_weeks: Optional[float] = None
    low_52_weeks: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
