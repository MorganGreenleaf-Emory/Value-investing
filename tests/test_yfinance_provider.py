"""Tests for YFinanceProvider's field-mapping logic.

These inject a fake yfinance module shaped like the real thing (verified by
reading the installed yfinance package's source, since this environment's
network policy blocks live calls to Yahoo Finance) rather than hitting the
network, so the mapping logic can be checked without live access.
"""

import pandas as pd
import pytest

from value_investing.providers.yfinance_provider import YFinanceProvider


class FakeTicker:
    def __init__(self, info, cashflow=None):
        self.info = info
        self._cashflow = cashflow if cashflow is not None else pd.DataFrame()

    @property
    def cashflow(self):
        return self._cashflow


class FakeYFinanceModule:
    def __init__(self, tickers):
        self._tickers = tickers

    def Ticker(self, symbol):
        return self._tickers[symbol]


def make_cashflow(operating_cash_flow, capital_expenditure):
    # Real yfinance columns are dates, most-recent first; only the first
    # column is read, so a single generic column is enough here.
    return pd.DataFrame(
        {"2025-12-31": [operating_cash_flow, capital_expenditure]},
        index=["Operating Cash Flow", "Capital Expenditure"],
    )


def test_maps_info_fields_onto_snapshot():
    info = {
        "currentPrice": 308.24,
        "trailingPE": 35.611202,
        "priceToBook": 40.5469,
        "dividendYield": 0.356682,
        "marketCap": 4527244176000,
        "fiftyTwoWeekHigh": 317.40,
        "fiftyTwoWeekLow": 201.50,
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }
    fake_yf = FakeYFinanceModule({"AAPL": FakeTicker(info)})
    provider = YFinanceProvider(yfinance_module=fake_yf)

    snapshots = provider.get_snapshots(["AAPL"])

    assert len(snapshots) == 1
    stock = snapshots[0]
    assert stock.symbol == "AAPL"
    assert stock.price == 308.24
    assert stock.pe_ratio == 35.611202
    assert stock.pb_ratio == 40.5469
    assert stock.dividend_yield == 0.356682
    assert stock.market_cap == 4527244176000
    assert stock.high_52_weeks == 317.40
    assert stock.low_52_weeks == 201.50
    assert stock.sector == "Technology"
    assert stock.industry == "Consumer Electronics"


def test_falls_back_to_regular_market_price_when_current_price_missing():
    info = {"regularMarketPrice": 83.98}
    fake_yf = FakeYFinanceModule({"KO": FakeTicker(info)})
    provider = YFinanceProvider(yfinance_module=fake_yf)

    snapshots = provider.get_snapshots(["KO"])

    assert snapshots[0].price == 83.98


def test_skips_ticker_with_no_price_at_all():
    fake_yf = FakeYFinanceModule({"NOPE": FakeTicker({})})
    provider = YFinanceProvider(yfinance_module=fake_yf)

    assert provider.get_snapshots(["NOPE"]) == []


def test_cash_flow_capex_sign_is_normalized_to_positive():
    # Yahoo reports capex as a negative outflow.
    info = {"currentPrice": 100.0}
    cashflow = make_cashflow(operating_cash_flow=111_482_000_000.0, capital_expenditure=-12_715_000_000.0)
    fake_yf = FakeYFinanceModule({"AAPL": FakeTicker(info, cashflow)})
    provider = YFinanceProvider(yfinance_module=fake_yf)

    stock = provider.get_snapshots(["AAPL"])[0]

    assert stock.operating_cash_flow == 111_482_000_000.0
    assert stock.capital_expenditures == 12_715_000_000.0  # sign flipped to positive


def test_missing_cash_flow_rows_leave_fields_none():
    info = {"currentPrice": 100.0}
    fake_yf = FakeYFinanceModule({"AAPL": FakeTicker(info, pd.DataFrame())})
    provider = YFinanceProvider(yfinance_module=fake_yf)

    stock = provider.get_snapshots(["AAPL"])[0]

    assert stock.operating_cash_flow is None
    assert stock.capital_expenditures is None


def test_requires_explicit_symbols():
    provider = YFinanceProvider(yfinance_module=FakeYFinanceModule({}))
    with pytest.raises(ValueError):
        provider.get_snapshots(None)


def test_raises_helpful_error_without_yfinance_installed(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yfinance":
            raise ImportError("no module named yfinance")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError, match="pip install yfinance"):
        YFinanceProvider()
