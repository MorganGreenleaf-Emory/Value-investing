from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import StockSnapshot


class DataProvider(ABC):
    """Anything that can turn a list of ticker symbols into StockSnapshots."""

    @abstractmethod
    def get_snapshots(self, symbols: Optional[List[str]]) -> List[StockSnapshot]:
        """Return a StockSnapshot per symbol. Pass None for symbols to mean
        'give me everything you have' (only meaningful for providers backed
        by a fixed dataset, like CSVProvider)."""
