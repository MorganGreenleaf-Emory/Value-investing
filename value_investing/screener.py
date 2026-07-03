"""Command-line entry point: score a set of tickers on value metrics.

    python -m value_investing.screener AAPL KO WFC
    python -m value_investing.screener --source robinhood AAPL KO WFC
    python -m value_investing.screener AAPL --growth-rate 0.05 --discount-rate 0.09
"""

import argparse
import sys
from typing import List, Optional

from .dcf import DCFAssumptions
from .providers.csv_provider import CSVProvider
from .scoring import ScoredStock, score_stocks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score stocks on classic value-investing metrics.")
    parser.add_argument("symbols", nargs="*", help="Ticker symbols to screen (default: every row in --csv)")
    parser.add_argument("--source", choices=["csv", "robinhood"], default="csv")
    parser.add_argument("--csv", default="data/sample_stocks.csv", help="Path to the CSV file when --source csv")
    parser.add_argument("--top", type=int, default=None, help="Only show the top N results")
    parser.add_argument(
        "--growth-rate", type=float, default=0.08, help="DCF: projected annual FCF growth rate (default 0.08)"
    )
    parser.add_argument(
        "--discount-rate", type=float, default=0.10, help="DCF: discount rate / required return (default 0.10)"
    )
    parser.add_argument(
        "--terminal-growth",
        type=float,
        default=0.025,
        help="DCF: perpetual growth rate after the projection window (default 0.025)",
    )
    parser.add_argument("--years", type=int, default=5, help="DCF: number of years explicitly projected (default 5)")
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.source == "csv":
        provider = CSVProvider(args.csv)
    else:
        from .providers.robinhood_provider import RobinhoodProvider

        provider = RobinhoodProvider()

    try:
        dcf_assumptions = DCFAssumptions(
            growth_rate=args.growth_rate,
            discount_rate=args.discount_rate,
            terminal_growth_rate=args.terminal_growth,
            years=args.years,
        )
        snapshots = provider.get_snapshots(args.symbols or None)
    except (ValueError, RuntimeError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not snapshots:
        print("No data found for the requested symbols.", file=sys.stderr)
        return 1

    scored = score_stocks(snapshots, dcf_assumptions=dcf_assumptions)
    if args.top:
        scored = scored[: args.top]

    print_table(scored)
    return 0


def print_table(scored: List[ScoredStock]) -> None:
    headers = [
        "Rank",
        "Symbol",
        "Score",
        "P/E",
        "P/B",
        "Div Yield %",
        "Graham MoS %",
        "DCF MoS %",
        "FCF Yield %",
        "Sector",
    ]
    rows = []
    for rank, r in enumerate(scored, start=1):
        d = r.details
        rows.append(
            [
                str(rank),
                r.symbol,
                f"{r.score:.1f}",
                _fmt(d.get("pe_ratio")),
                _fmt(d.get("pb_ratio")),
                _fmt(d.get("dividend_yield")),
                _fmt(d.get("graham_margin_of_safety"), as_pct=True),
                _fmt(d.get("dcf_margin_of_safety"), as_pct=True),
                _fmt(d.get("fcf_yield"), as_pct=True),
                r.stock.sector or "-",
            ]
        )

    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]

    def fmt_row(row: List[str]) -> str:
        return "  ".join(cell.ljust(w) for cell, w in zip(row, widths))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt_row(row))


def _fmt(value: Optional[float], as_pct: bool = False) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}" if as_pct else f"{value:.2f}"


if __name__ == "__main__":
    sys.exit(run())
