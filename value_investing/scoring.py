"""Cross-sectional value score: rank each stock against the others being
screened on a handful of value metrics, then combine those ranks into a
single 0-100 score.

Ranking within the given universe (rather than against fixed thresholds)
means the score is only meaningful relative to the set of symbols you pass
in — screening 5 mega-cap tech stocks together will rank them very
differently than screening those same 5 alongside a basket of deep-value
bank stocks.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import metrics
from .dcf import DCFAssumptions, dcf_margin_of_safety
from .models import StockSnapshot


@dataclass
class ScoredStock:
    symbol: str
    stock: StockSnapshot
    score: float
    details: Dict[str, Optional[float]] = field(default_factory=dict)


# (name, extractor, weight, lower_is_better). Two independent value-vs-price
# signals feed the score: graham_margin_of_safety (mechanical, ratio-based)
# and dcf_margin_of_safety (assumption-driven, cash-flow-based).
_METRIC_DEFINITIONS: List[tuple] = [
    ("pe_ratio", lambda s: s.pe_ratio if s.pe_ratio and s.pe_ratio > 0 else None, 0.15, True),
    ("pb_ratio", lambda s: s.pb_ratio if s.pb_ratio and s.pb_ratio > 0 else None, 0.15, True),
    ("dividend_yield", lambda s: s.dividend_yield, 0.15, False),
    ("graham_margin_of_safety", metrics.margin_of_safety, 0.15, False),
    ("price_position_in_52w_range", metrics.price_position_in_52w_range, 0.10, True),
    ("fcf_yield", metrics.fcf_yield, 0.10, False),
    ("dcf_margin_of_safety", 0.20, False),
]


def _percentile_ranks(values: List[tuple]) -> Dict[int, float]:
    """values: list of (index, value). Returns index -> rank in [0, 1],
    where 1 means the highest value in the set. A lone data point (or an
    empty set) can't be ranked against anything, so it gets a neutral 0.5.
    """
    n = len(values)
    if n == 0:
        return {}
    if n == 1:
        return {values[0][0]: 0.5}
    ranks = {}
    for rank, (idx, _) in enumerate(sorted(values, key=lambda kv: kv[1])):
        ranks[idx] = rank / (n - 1)
    return ranks


def _build_metric_definitions(dcf_assumptions: Optional[DCFAssumptions]) -> List[tuple]:
    """dcf_margin_of_safety needs the caller's assumptions bound into its
    extractor, so it's assembled here rather than defined statically."""
    definitions = list(_METRIC_DEFINITIONS[:-1])
    _, weight, lower_is_better = _METRIC_DEFINITIONS[-1]
    definitions.append(
        ("dcf_margin_of_safety", lambda s: dcf_margin_of_safety(s, dcf_assumptions), weight, lower_is_better)
    )
    return definitions


def score_stocks(
    stocks: List[StockSnapshot], dcf_assumptions: Optional[DCFAssumptions] = None
) -> List[ScoredStock]:
    metric_definitions = _build_metric_definitions(dcf_assumptions)

    metric_ranks: Dict[str, Dict[int, float]] = {}
    for name, extractor, _weight, lower_is_better in metric_definitions:
        available = [(i, v) for i, s in enumerate(stocks) if (v := extractor(s)) is not None]
        ranks = _percentile_ranks(available)
        if lower_is_better:
            ranks = {i: 1 - r for i, r in ranks.items()}
        metric_ranks[name] = ranks

    results = []
    for i, stock in enumerate(stocks):
        weighted_sum = 0.0
        total_weight = 0.0
        details: Dict[str, Optional[float]] = {}
        for name, extractor, weight, _lower_is_better in metric_definitions:
            details[name] = extractor(stock)
            rank = metric_ranks[name].get(i)
            if rank is not None:
                weighted_sum += rank * weight
                total_weight += weight
        score = (weighted_sum / total_weight * 100) if total_weight > 0 else 0.0
        results.append(ScoredStock(symbol=stock.symbol, stock=stock, score=round(score, 1), details=details))

    results.sort(key=lambda r: r.score, reverse=True)
    return results
