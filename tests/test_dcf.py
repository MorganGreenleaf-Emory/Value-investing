import pytest

from value_investing.dcf import DCFAssumptions, dcf_fair_value, dcf_margin_of_safety
from value_investing.models import StockSnapshot


def make_stock(**overrides) -> StockSnapshot:
    defaults = dict(
        symbol="TEST",
        price=100.0,
        market_cap=1000.0,  # -> 10 shares outstanding
        operating_cash_flow=150.0,
        capital_expenditures=50.0,  # -> FCF = 100.0
    )
    defaults.update(overrides)
    return StockSnapshot(**defaults)


def test_dcf_assumptions_rejects_discount_rate_below_terminal_growth():
    with pytest.raises(ValueError):
        DCFAssumptions(discount_rate=0.02, terminal_growth_rate=0.03)


def test_dcf_assumptions_rejects_non_positive_years():
    with pytest.raises(ValueError):
        DCFAssumptions(years=0)


def test_dcf_fair_value_none_without_fcf():
    stock = make_stock(operating_cash_flow=None)
    assert dcf_fair_value(stock) is None


def test_dcf_fair_value_none_without_market_cap():
    stock = make_stock(market_cap=None)
    assert dcf_fair_value(stock) is None


def test_dcf_fair_value_matches_hand_computation():
    # FCF = 100, 10 shares outstanding, 0% growth/terminal growth so the
    # math reduces to a plain growing perpetuity, easy to check by hand.
    assumptions = DCFAssumptions(growth_rate=0.0, discount_rate=0.10, terminal_growth_rate=0.0, years=1)
    stock = make_stock()

    result = dcf_fair_value(stock, assumptions)

    assert result is not None
    assert result.shares_outstanding == 10.0
    # Year 1 FCF stays 100 (0% growth); PV = 100 / 1.10
    assert result.projected_fcf == [100.0]
    assert round(result.present_value_of_projected_fcf, 4) == round(100 / 1.10, 4)
    # Terminal value = 100 * 1.0 / (0.10 - 0.0) = 1000, discounted 1 year
    assert round(result.terminal_value, 4) == 1000.0
    assert round(result.present_value_of_terminal_value, 4) == round(1000 / 1.10, 4)

    equity_value = result.present_value_of_projected_fcf + result.present_value_of_terminal_value
    assert round(result.fair_value_per_share, 4) == round(equity_value / 10.0, 4)


def test_dcf_margin_of_safety_positive_when_market_cap_below_intrinsic_value():
    # Fair value per share = intrinsic equity value * price / market_cap, so
    # margin of safety reduces to a comparison of market_cap vs. the DCF's
    # implied equity value -- price alone (with market_cap held constant)
    # doesn't move it, since shares_outstanding is derived from both.
    stock = make_stock(market_cap=500.0)  # well below the ~$1000+ intrinsic equity value
    mos = dcf_margin_of_safety(stock)
    assert mos is not None
    assert mos > 0


def test_dcf_margin_of_safety_negative_when_market_cap_above_intrinsic_value():
    stock = make_stock(market_cap=100_000.0)
    mos = dcf_margin_of_safety(stock)
    assert mos is not None
    assert mos < 0


def test_apple_fy2025_dcf():
    # Same real AAPL inputs used for the FCF test: FY2025 10-K operating
    # cash flow $111.482B, capex $12.715B -> FCF ~$98.77B. Market cap/price
    # are an intraday Robinhood snapshot from 2026-07-02.
    aapl = make_stock(
        symbol="AAPL",
        price=308.24,
        market_cap=4_527_244_176_000.0,
        operating_cash_flow=111_482_000_000.0,
        capital_expenditures=12_715_000_000.0,
    )
    result = dcf_fair_value(aapl)
    assert result is not None
    assert result.fair_value_per_share > 0
    # Shares outstanding backed out of market cap / price should roughly
    # match Apple's actual ~14.69B shares outstanding.
    assert 14.5e9 < result.shares_outstanding < 14.9e9
