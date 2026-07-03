# Value Investing Screener

A small, learning-focused Python tool that scores stocks on classic
value-investing metrics — cheapness relative to earnings and book value,
dividend yield, margin of safety versus a Graham Number fair-value estimate,
and where the price sits in its 52-week range.

This is an educational project, not investment advice. The scoring model is
a simple heuristic, not a recommendation engine.

## How it works

1. A **provider** fetches a `StockSnapshot` (price, P/E, P/B, dividend
   yield, 52-week range, sector) for each ticker you ask about — either
   from a local CSV (`CSVProvider`) or live from Robinhood
   (`RobinhoodProvider`, via the `robin_stocks` library).
2. `value_investing/metrics.py` derives value metrics from that snapshot:
   - **EPS** and **book value per share**, backed out of price ÷ P/E and
     price ÷ P/B (Robinhood's fundamentals endpoint doesn't expose these
     directly).
   - **Graham Number** — Benjamin Graham's rule-of-thumb fair value,
     `sqrt(22.5 * EPS * book value per share)`.
   - **Margin of safety** — how far the current price sits below (or
     above) the Graham Number, as a fraction.
   - **Price position in 52-week range** — 0.0 at the 52-week low, 1.0 at
     the 52-week high.
3. `value_investing/scoring.py` ranks every stock in the batch against the
   others on each metric (cheaper P/E, cheaper P/B, higher dividend yield,
   higher margin of safety, lower position in the 52-week range are all
   "better"), and combines the ranks into a single 0-100 score. **The
   score is only meaningful relative to the set of tickers you screen
   together** — it's a relative ranking, not an absolute one.

## Setup

```bash
pip install -r requirements-dev.txt   # includes pytest for running tests
```

## Usage

Offline, using the bundled sample data (`data/sample_stocks.csv`, a
snapshot of 10 real tickers):

```bash
python -m value_investing.screener AAPL MSFT KO WFC T VZ
python -m value_investing.screener            # screens every row in the CSV
python -m value_investing.screener --top 5    # only show the top 5
```

Live, via your own Robinhood account:

```bash
cp .env.example .env   # fill in ROBINHOOD_USERNAME / ROBINHOOD_PASSWORD
export $(cat .env | xargs)
python -m value_investing.screener --source robinhood AAPL MSFT KO WFC
```

(`robin_stocks` will prompt interactively for an SMS/app MFA code on first
login.)

Bring your own watchlist by editing `data/sample_stocks.csv` or pointing
`--csv` at your own file with the same columns:

```
symbol,price,pe_ratio,pb_ratio,dividend_yield,market_cap,high_52_weeks,low_52_weeks,sector,industry
```

Any column besides `symbol` and `price` can be left blank — metrics that
need a missing input are simply excluded from that stock's score instead
of crashing.

## Running tests

```bash
pytest
```

## Project layout

```
value_investing/
  models.py               StockSnapshot data model
  metrics.py               EPS, book value, Graham Number, margin of safety
  scoring.py                Cross-sectional ranking -> 0-100 value score
  screener.py               CLI entry point
  providers/
    csv_provider.py         Reads snapshots from a CSV file
    robinhood_provider.py   Reads snapshots live via robin_stocks
data/sample_stocks.csv      Sample offline dataset
tests/                       pytest unit tests for metrics + scoring
```

## Ideas for extending this

- Add more metrics: Piotroski F-Score, free cash flow yield, debt/equity
  (would need a data source with full financial statements, since
  Robinhood's fundamentals endpoint doesn't include these).
- Track a watchlist's score over time instead of a single point-in-time
  screen.
- Weight metrics by sector (e.g. banks structurally carry more leverage,
  so a straight debt/equity comparison against tech companies is
  misleading).
