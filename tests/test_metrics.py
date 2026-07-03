from value_investing.metrics import (
    book_value_per_share,
    earnings_per_share,
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
