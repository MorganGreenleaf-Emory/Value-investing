import csv
from typing import List, Optional

from ..models import StockSnapshot
from .base import DataProvider


def _to_float(value) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


class CSVProvider(DataProvider):
    """Reads StockSnapshots from a local CSV file. Useful for learning and
    testing without needing a live brokerage connection.

    Expected columns: symbol,price,pe_ratio,pb_ratio,dividend_yield,
    market_cap,high_52_weeks,low_52_weeks,sector,industry,
    operating_cash_flow,capital_expenditures
    All columns besides symbol and price may be left blank.
    """

    def __init__(self, path: str):
        self.path = path

    def get_snapshots(self, symbols: Optional[List[str]]) -> List[StockSnapshot]:
        wanted = {s.upper() for s in symbols} if symbols else None
        snapshots = []
        with open(self.path, newline="") as f:
            for row in csv.DictReader(f):
                symbol = row["symbol"].strip().upper()
                if wanted is not None and symbol not in wanted:
                    continue
                snapshots.append(
                    StockSnapshot(
                        symbol=symbol,
                        price=float(row["price"]),
                        pe_ratio=_to_float(row.get("pe_ratio")),
                        pb_ratio=_to_float(row.get("pb_ratio")),
                        dividend_yield=_to_float(row.get("dividend_yield")),
                        market_cap=_to_float(row.get("market_cap")),
                        high_52_weeks=_to_float(row.get("high_52_weeks")),
                        low_52_weeks=_to_float(row.get("low_52_weeks")),
                        sector=row.get("sector") or None,
                        industry=row.get("industry") or None,
                        operating_cash_flow=_to_float(row.get("operating_cash_flow")),
                        capital_expenditures=_to_float(row.get("capital_expenditures")),
                    )
                )

        if wanted is not None:
            missing = wanted - {s.symbol for s in snapshots}
            if missing:
                raise ValueError(f"Symbols not found in {self.path}: {', '.join(sorted(missing))}")
        return snapshots
