import os
from typing import List, Optional

from ..models import StockSnapshot
from .base import DataProvider


def _to_float(value) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class RobinhoodProvider(DataProvider):
    """Fetches live fundamentals + quotes via the robin_stocks library.

    Requires a Robinhood account. Set ROBINHOOD_USERNAME and
    ROBINHOOD_PASSWORD (see .env.example) before use; robin_stocks will
    prompt interactively for an SMS/app MFA code on first login.
    """

    def __init__(self):
        try:
            import robin_stocks.robinhood as rh
        except ImportError as exc:
            raise ImportError(
                "robin_stocks is required for the Robinhood provider. Install it with: "
                "pip install robin_stocks"
            ) from exc
        self._rh = rh
        self._logged_in = False

    def _login(self) -> None:
        if self._logged_in:
            return
        username = os.environ.get("ROBINHOOD_USERNAME")
        password = os.environ.get("ROBINHOOD_PASSWORD")
        if not username or not password:
            raise RuntimeError(
                "Set ROBINHOOD_USERNAME and ROBINHOOD_PASSWORD environment variables "
                "(see .env.example) before using RobinhoodProvider."
            )
        self._rh.login(username, password)
        self._logged_in = True

    def get_snapshots(self, symbols: Optional[List[str]]) -> List[StockSnapshot]:
        if not symbols:
            raise ValueError("RobinhoodProvider requires an explicit list of symbols.")
        self._login()

        fundamentals = self._rh.get_fundamentals(symbols)
        prices = self._rh.get_latest_price(symbols)

        snapshots = []
        for symbol, data, price in zip(symbols, fundamentals, prices):
            if not data or price is None:
                continue
            snapshots.append(
                StockSnapshot(
                    symbol=symbol.upper(),
                    price=float(price),
                    pe_ratio=_to_float(data.get("pe_ratio")),
                    pb_ratio=_to_float(data.get("pb_ratio")),
                    dividend_yield=_to_float(data.get("dividend_yield")),
                    market_cap=_to_float(data.get("market_cap")),
                    high_52_weeks=_to_float(data.get("high_52_weeks")),
                    low_52_weeks=_to_float(data.get("low_52_weeks")),
                    sector=data.get("sector") or None,
                    industry=data.get("industry") or None,
                )
            )
        return snapshots
