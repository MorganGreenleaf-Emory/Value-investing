"""Discounted cash flow (DCF) valuation.

Unlike the Graham Number, a DCF can't be computed from ratios alone — it
requires explicit assumptions about future growth and a discount rate.
Rather than hide those behind a single "fair value" number, this module
takes them as an explicit, overridable DCFAssumptions object so it's clear
what's driving the result.

Method: project free cash flow forward at a constant growth rate for
`years`, discount each projected year back to the present, add a terminal
value (Gordon growth / perpetuity formula) for everything after the
projection window, and divide the total by shares outstanding.
"""

from dataclasses import dataclass
from typing import List, Optional

from .metrics import free_cash_flow
from .models import StockSnapshot


@dataclass
class DCFAssumptions:
    growth_rate: float = 0.08  # projected annual FCF growth during the projection window
    discount_rate: float = 0.10  # required rate of return (a WACC proxy)
    terminal_growth_rate: float = 0.025  # perpetual growth rate assumed after the projection window
    years: int = 5

    def __post_init__(self):
        if self.discount_rate <= self.terminal_growth_rate:
            raise ValueError("discount_rate must be greater than terminal_growth_rate")
        if self.years < 1:
            raise ValueError("years must be at least 1")


@dataclass
class DCFResult:
    fair_value_per_share: float
    shares_outstanding: float
    projected_fcf: List[float]
    present_value_of_projected_fcf: float
    terminal_value: float
    present_value_of_terminal_value: float
    assumptions: DCFAssumptions


def dcf_fair_value(stock: StockSnapshot, assumptions: Optional[DCFAssumptions] = None) -> Optional[DCFResult]:
    assumptions = assumptions or DCFAssumptions()

    fcf = free_cash_flow(stock)
    if fcf is None or fcf <= 0:
        return None
    if not stock.market_cap or stock.market_cap <= 0 or not stock.price or stock.price <= 0:
        return None

    shares_outstanding = stock.market_cap / stock.price

    projected_fcf = []
    pv_of_projected = 0.0
    current_fcf = fcf
    for year in range(1, assumptions.years + 1):
        current_fcf *= 1 + assumptions.growth_rate
        projected_fcf.append(current_fcf)
        pv_of_projected += current_fcf / (1 + assumptions.discount_rate) ** year

    terminal_value = (
        projected_fcf[-1]
        * (1 + assumptions.terminal_growth_rate)
        / (assumptions.discount_rate - assumptions.terminal_growth_rate)
    )
    pv_of_terminal = terminal_value / (1 + assumptions.discount_rate) ** assumptions.years

    equity_value = pv_of_projected + pv_of_terminal
    fair_value_per_share = equity_value / shares_outstanding

    return DCFResult(
        fair_value_per_share=fair_value_per_share,
        shares_outstanding=shares_outstanding,
        projected_fcf=projected_fcf,
        present_value_of_projected_fcf=pv_of_projected,
        terminal_value=terminal_value,
        present_value_of_terminal_value=pv_of_terminal,
        assumptions=assumptions,
    )


def dcf_margin_of_safety(stock: StockSnapshot, assumptions: Optional[DCFAssumptions] = None) -> Optional[float]:
    """Fractional discount of price to DCF fair value. Positive = undervalued."""
    result = dcf_fair_value(stock, assumptions)
    if result is None or result.fair_value_per_share <= 0:
        return None
    return (result.fair_value_per_share - stock.price) / result.fair_value_per_share
