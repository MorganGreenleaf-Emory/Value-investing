from value_investing.models import StockSnapshot
from value_investing.scoring import score_stocks


def test_cheaper_stock_scores_higher():
    cheap = StockSnapshot(
        symbol="CHEAP",
        price=20.0,
        pe_ratio=6.0,
        pb_ratio=1.0,
        dividend_yield=6.0,
        high_52_weeks=25.0,
        low_52_weeks=15.0,
    )
    expensive = StockSnapshot(
        symbol="PRICEY",
        price=300.0,
        pe_ratio=40.0,
        pb_ratio=15.0,
        dividend_yield=0.3,
        high_52_weeks=320.0,
        low_52_weeks=150.0,
    )

    scored = score_stocks([cheap, expensive])

    assert [s.symbol for s in scored] == ["CHEAP", "PRICEY"]
    assert scored[0].score > scored[1].score


def test_missing_metrics_score_zero_instead_of_crashing():
    stock = StockSnapshot(symbol="THIN", price=50.0)
    scored = score_stocks([stock])
    assert scored[0].symbol == "THIN"
    assert scored[0].score == 0.0


def test_lone_stock_with_partial_data_gets_neutral_score():
    # Only two of five metrics are available, and with nothing to rank
    # against, each should land at the neutral midpoint (0.5).
    stock = StockSnapshot(symbol="ONLY", price=50.0, pe_ratio=10.0, pb_ratio=1.0)
    scored = score_stocks([stock])
    assert scored[0].score == 50.0


def test_results_sorted_descending():
    stocks = [
        StockSnapshot(symbol="A", price=50.0, pe_ratio=30.0, pb_ratio=10.0),
        StockSnapshot(symbol="B", price=50.0, pe_ratio=8.0, pb_ratio=1.0),
        StockSnapshot(symbol="C", price=50.0, pe_ratio=15.0, pb_ratio=3.0),
    ]
    scored = score_stocks(stocks)
    scores = [s.score for s in scored]
    assert scores == sorted(scores, reverse=True)
