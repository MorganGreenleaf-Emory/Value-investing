from dataclasses import dataclass
from typing import Optional


@dataclass
class StockSnapshot:
    """A point-in-time snapshot of the data needed to value a stock.

    Fields mirror what's available from Robinhood's fundamentals + quote
    endpoints, since that's the primary data source. Anything not known
    should be left as None rather than guessed.
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
