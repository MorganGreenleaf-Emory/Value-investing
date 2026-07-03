"""Value-investing metrics derived from a StockSnapshot.

Robinhood's fundamentals endpoint doesn't expose raw EPS or book value per
share directly, but both can be backed out of price, P/E, and P/B. Everything
here returns None instead of raising when the inputs needed for a metric
aren't available or wouldn't make sense (e.g. a negative P/E from negative
earnings).
"""

from math import sqrt
from typing import Optional

from .models import StockSnapshot


def earnings_per_share(stock: StockSnapshot) -> Optional[float]:
    if not stock.pe_ratio or stock.pe_ratio <= 0:
        return None
    return stock.price / stock.pe_ratio


def book_value_per_share(stock: StockSnapshot) -> Optional[float]:
    if not stock.pb_ratio or stock.pb_ratio <= 0:
        return None
    return stock.price / stock.pb_ratio


def graham_number(stock: StockSnapshot) -> Optional[float]:
    """Benjamin Graham's rule-of-thumb fair value: sqrt(22.5 * EPS * BVPS)."""
    eps = earnings_per_share(stock)
    bvps = book_value_per_share(stock)
    if eps is None or bvps is None or eps <= 0 or bvps <= 0:
        return None
    return sqrt(22.5 * eps * bvps)


def margin_of_safety(stock: StockSnapshot) -> Optional[float]:
    """Fractional discount of price to Graham Number. Positive = undervalued."""
    gn = graham_number(stock)
    if gn is None or gn <= 0:
        return None
    return (gn - stock.price) / gn


def price_position_in_52w_range(stock: StockSnapshot) -> Optional[float]:
    """0.0 = sitting at the 52-week low, 1.0 = sitting at the 52-week high."""
    if stock.high_52_weeks is None or stock.low_52_weeks is None:
        return None
    span = stock.high_52_weeks - stock.low_52_weeks
    if span <= 0:
        return None
    return (stock.price - stock.low_52_weeks) / span
