from value_investing.metrics import (
    book_value_per_share,
    earnings_per_share,
    fcf_yield,
    free_cash_flow,
    graham_number,
    margin_of_safety,
    price_position_in_52w_range,
)
from value_investing.models import StockSnapshot


def make_stock(**overrides) -> StockSnapshot:
    defaults = dict(symbol="TEST", price=100.0)
    defaults.update(overrides)
    return StockSnapshot(**defaults)


def test_earnings_per_share():
    assert earnings_per_share(make_stock(price=100.0, pe_ratio=20.0)) == 5.0


def test_earnings_per_share_none_when_pe_missing():
    assert earnings_per_share(make_stock(pe_ratio=None)) is None


def test_earnings_per_share_none_when_pe_negative():
    assert earnings_per_share(make_stock(pe_ratio=-192.16)) is None


def test_book_value_per_share():
    assert book_value_per_share(make_stock(price=100.0, pb_ratio=4.0)) == 25.0


def test_book_value_per_share_none_when_pb_missing():
    assert book_value_per_share(make_stock(pb_ratio=None)) is None


def test_graham_number():
    # eps=5, bvps=25 -> sqrt(22.5 * 5 * 25) = sqrt(2812.5)
    gn = graham_number(make_stock(price=100.0, pe_ratio=20.0, pb_ratio=4.0))
    assert gn is not None
    assert round(gn, 2) == 53.03


def test_graham_number_none_without_pe():
    assert graham_number(make_stock(pe_ratio=None, pb_ratio=4.0)) is None


def test_margin_of_safety_positive_when_undervalued():
    # eps=5, bvps=25 -> graham number ~53.03, well above a price of 40
    stock = make_stock(price=40.0, pe_ratio=8.0, pb_ratio=1.6)
    mos = margin_of_safety(stock)
    assert mos is not None
    assert mos > 0


def test_margin_of_safety_negative_when_overvalued():
    stock = make_stock(price=100.0, pe_ratio=20.0, pb_ratio=4.0)
    mos = margin_of_safety(stock)
    assert mos is not None
    assert mos < 0


def test_price_position_in_52w_range():
    stock = make_stock(price=75.0, high_52_weeks=100.0, low_52_weeks=50.0)
    assert price_position_in_52w_range(stock) == 0.5


def test_price_position_none_without_range():
    assert price_position_in_52w_range(make_stock(high_52_weeks=None, low_52_weeks=50.0)) is None


def test_free_cash_flow():
    stock = make_stock(operating_cash_flow=100.0, capital_expenditures=30.0)
    assert free_cash_flow(stock) == 70.0


def test_free_cash_flow_none_without_both_inputs():
    assert free_cash_flow(make_stock(operating_cash_flow=100.0, capital_expenditures=None)) is None
    assert free_cash_flow(make_stock(operating_cash_flow=None, capital_expenditures=30.0)) is None


def test_fcf_yield():
    stock = make_stock(market_cap=1000.0, operating_cash_flow=100.0, capital_expenditures=30.0)
    assert fcf_yield(stock) == 0.07


def test_fcf_yield_none_without_market_cap():
    stock = make_stock(market_cap=None, operating_cash_flow=100.0, capital_expenditures=30.0)
    assert fcf_yield(stock) is None


def test_apple_fy2025_free_cash_flow():
    # Real figures from Apple's FY2025 10-K (year ended 2025-09-27):
    # operating cash flow $111.482B, capex $12.715B -> FCF ~$98.77B.
    # Market cap and price are an intraday Robinhood snapshot from 2026-07-02.
    aapl = make_stock(
        symbol="AAPL",
        price=308.24,
        market_cap=4_527_244_176_000.0,
        operating_cash_flow=111_482_000_000.0,
        capital_expenditures=12_715_000_000.0,
    )
    fcf = free_cash_flow(aapl)
    assert fcf is not None
    assert round(fcf / 1e9, 2) == 98.77

    yld = fcf_yield(aapl)
    assert yld is not None
    assert round(yld * 100, 2) == 2.18
