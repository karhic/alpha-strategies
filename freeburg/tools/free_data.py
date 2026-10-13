"""Conservative user-side Freeburg data import/validation tools.

No market data are redistributed by this module. Imports are written locally,
and replacements are never silently promoted to benchmark status.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import re
from statistics import median
import urllib.request


def _date(s: str) -> date:
    return date.fromisoformat(str(s).strip()[:10])


def _float(s: object) -> float | None:
    if s is None:
        return None
    v = str(s).strip().replace(",", "")
    if not v or v in {".", "-", "N/A", "nan", "None", "......", "……"}:
        return None
    # Published tables prefix provisional figures with p/r and may use a
    # Unicode ellipsis for missing values. Do not turn missing into zero.
    v = re.sub(r"^(?:p|r)\s+(?=[+-]?\d)", "", v, flags=re.I)
    try:
        x = float(v)
    except ValueError:
        return None
    if not (-1e100 < x < 1e100):
        return None
    return x


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_prices(path: Path) -> dict[date, float]:
    """Accept Date/Close or date/spx; normalize any daily or weekly CSV to W-FRI."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = {h.lower().strip(): h for h in (reader.fieldnames or [])}
        dcol = cols.get("date")
        vcol = cols.get("close") or cols.get("spx")
        if not dcol or not vcol:
            raise ValueError("Expected date and close (or spx) columns")
        observed: dict[date, float] = {}
        for row in reader:
            try:
                day = _date(row[dcol])
            except (ValueError, TypeError):
                continue
            value = _float(row[vcol])
            if value is None or value <= 0:
                continue
            if day in observed and abs(observed[day] - value) > 1e-8:
                raise ValueError(f"Conflicting close for {day}")
            observed[day] = value
    if not observed:
        raise ValueError(f"No valid positive prices in {path}")
    # Last observation in each Friday-ending week, with no missing-week interpolation.
    weeks: dict[date, tuple[date, float]] = {}
    for d, v in sorted(observed.items()):
        friday = d + timedelta(days=(4 - d.weekday()) % 7)
        current = weeks.get(friday)
        if current is None or d > current[0]:
            weeks[friday] = (d, v)
    return {d: obs[1] for d, obs in sorted(weeks.items())}


def prices_to_file(src: Path, out: Path) -> dict:
    prices = load_prices(src)
    rows = [{"date": d.isoformat(), "spx": f"{v:.12g}"} for d, v in prices.items()]
    _write_csv(out, ["date", "spx"], rows)
    return {"source": str(src), "output": str(out), "weeks": len(prices),
            "first": min(prices).isoformat(), "last": max(prices).isoformat(),
            "status": "LOCAL_ALTERNATIVE_NOT_BENCHMARK"}


def price_comparison(candidate: Path, baseline: Path, tolerance_bps: float = 1.) -> dict:
    if tolerance_bps < 0:
        raise ValueError("tolerance_bps must be >= 0")
    a = load_prices(candidate)
    b = load_prices(baseline)
    days = sorted(set(a) & set(b))
    if not days:
        raise ValueError("No common weekly dates")
    errors = [(d, (a[d] / b[d] - 1) * 10000) for d in days]
    bad = [(d, x) for d, x in errors if abs(x) > tolerance_bps]
    abs_errors = sorted(abs(x) for _, x in errors)

    def risk_state(series: dict[date, float], n: int = 52) -> dict[date, bool]:
        dates = sorted(series)
        return {d: series[d] > sum(series[x] for x in dates[i-n+1:i+1]) / n
                for i, d in enumerate(dates) if i >= n-1}

    sta = risk_state(a)
    stb = risk_state(b)
    comparable = sorted(set(sta) & set(stb))
    mismatched = [d.isoformat() for d in comparable if sta[d] != stb[d]]
    return {
        "candidate": str(candidate), "baseline": str(baseline),
        "overlap_weeks": len(days), "candidate_weeks": len(a), "baseline_weeks": len(b),
        "tolerance_bps": tolerance_bps, "over_tolerance": len(bad),
        "median_abs_bps": round(median(abs_errors), 5),
        "max_abs_bps": round(max(abs_errors), 5),
        "worst_dates": [{"date": d.isoformat(), "signed_bps": round(x, 4)}
                        for d, x in sorted(errors, key=lambda z: -abs(z[1]))[:10]],
        "ma52_comparable_weeks": len(comparable),
        "ma52_state_disagreements": len(mismatched),
        "ma52_first_disagreements": mismatched[:10],
        "status": "COMPARISON_ONLY_DO_NOT_SILENTLY_REPLACE",
    }


def govinfo_urls(issue: str, page: str) -> dict:
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])|199[5-9]-(0[1-9]|1[0-2])", issue):
        raise ValueError("Issue must be YYYY-MM, from April 1995 onward")
    if issue < "1995-04":
        raise ValueError("GovInfo Economic Indicators starts April 1995")
    if not re.fullmatch(r"\d{1,3}(?:-1)?", page):
        raise ValueError("Page must be numeric PgN (optional -1), e.g. 31")
    pkg = f"ECONI-{issue}"
    gran = f"{pkg}-Pg{page}"
    base = f"https://www.govinfo.gov/content/pkg/{pkg}"
    return {"issue": issue, "page": page,
            "details": f"https://www.govinfo.gov/app/details/{pkg}/{gran}",
            "xls": f"{base}/xls/{gran}.xls",
            "html": f"{base}/html/{gran}.htm",
            "warning": "Verify correct stock-table page and actual publication date independently."}


def govinfo_download(issue: str, page: str, dest: Path) -> dict:
    url = govinfo_urls(issue, page)["xls"]
    if dest.exists():
        raise FileExistsError(f"Refusing to overwrite {dest}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Freeburg-Research/1.0 (manual single-table download)"})
    with urllib.request.urlopen(req, timeout=35) as response:
        data = response.read(4 * 1024 * 1024 + 1)
    if len(data) > 4 * 1024 * 1024:
        raise ValueError("Unexpected >4MB single table")
    if not data.startswith(b"\xd0\xcf\x11\xe0") and not data.startswith(b"PK\x03\x04"):
        raise ValueError("Not an Excel binary/ZIP file; check page and access")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return {"saved": str(dest), "bytes": len(data), "source_url": url}


def govinfo_preview(path: Path, sheet: int = 0, max_rows: int = 26) -> list[list[str]]:
    """Read local GovInfo spreadsheet for inspection; never guess column identity."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("Install pandas and xlrd for .xls (openpyxl for .xlsx)") from exc
    df = pd.read_excel(path, sheet_name=sheet, header=None, dtype=str)
    return [["" if pd.isna(v) else str(v) for v in row]
            for row in df.head(max_rows).itertuples(index=False, name=None)]


MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def parse_govinfo_monthly_rows(rows: list[list[str]], *, period_col: int,
                                dividend_col: int, earnings_col: int,
                                published_on: date, source_url: str) -> list[dict]:
    """Extract explicitly labelled monthly rows only.

    published_on must be independently verified, never inferred from issue name.
    No point-in-time availability is asserted by the output.
    """
    current_year: int | None = None
    out = []
    for rownum, row in enumerate(rows, 1):
        if max(period_col, dividend_col, earnings_col) >= len(row):
            continue
        label = str(row[period_col]).strip()
        full = re.fullmatch(r"((?:19|20)\d{2}):\s*([A-Za-z]{3,9})\.?", label)
        short = re.fullmatch(r"([A-Za-z]{3,9})\.?", label)
        if full:
            current_year = int(full.group(1))
            mon = MONTHS.get(full.group(2)[:3].lower())
        elif short and current_year:
            mon = MONTHS.get(short.group(1)[:3].lower())
        else:
            continue
        if not mon or not current_year:
            continue
        period = date(current_year, mon, 1)
        if period > published_on:
            continue
        div = _float(row[dividend_col])
        earn = _float(row[earnings_col])
        if div is None and earn is None:
            continue
        if div is not None and not (0 < div < 25):
            raise ValueError(f"Implausible dividend yield at row {rownum}: {div}")
        if earn is not None and not (-30 < earn < 50):
            raise ValueError(f"Implausible earnings yield at row {rownum}: {earn}")
        out.append({"published_on": published_on.isoformat(),
                    "period_date": period.isoformat(),
                    "dividend_yield_percent": "" if div is None else div,
                    "earnings_yield_percent": "" if earn is None else earn,
                    "source_url": source_url, "source_row": rownum,
                    "status": "PRELIMINARY_PUBLISH_DATE_MUST_BE_VERIFIED"})
    return out


def govinfo_extract(args) -> dict:
    rows = govinfo_preview(args.input, sheet=args.sheet, max_rows=10000)
    extracted = parse_govinfo_monthly_rows(
        rows, period_col=args.period_col, dividend_col=args.dividend_col,
        earnings_col=args.earnings_col, published_on=_date(args.published_on),
        source_url=args.source_url)
    if not extracted:
        raise ValueError("No rows recognized. Use govinfo-preview to check page and column indexes")
    _write_csv(args.output, ["published_on", "period_date", "dividend_yield_percent",
                             "earnings_yield_percent", "source_url", "source_row", "status"], extracted)
    return {"rows": len(extracted), "output": str(args.output),
            "warning": "Not automatically PIT-qualified; manually verify actual public release date."}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import-prices", help="Normalize user-obtained daily/weekly CSV to Friday weeks")
    imp.add_argument("--input", type=Path, required=True)
    imp.add_argument("--output", type=Path, required=True)
    cmp = sub.add_parser("compare-prices", help="Compare candidate to frozen reference and MA52 state")
    cmp.add_argument("--candidate", type=Path, required=True)
    cmp.add_argument("--baseline", type=Path, required=True)
    cmp.add_argument("--tolerance-bps", type=float, default=1.)
    urls = sub.add_parser("govinfo-urls", help="Construct official Economic Indicators table URLs")
    urls.add_argument("--issue", required=True)
    urls.add_argument("--page", required=True)
    dl = sub.add_parser("govinfo-download", help="Download one explicitly selected official XLS")
    dl.add_argument("--issue", required=True)
    dl.add_argument("--page", required=True)
    dl.add_argument("--output", type=Path, required=True)
    prev = sub.add_parser("govinfo-preview", help="Inspect local XLS with row/column indexes")
    prev.add_argument("--input", type=Path, required=True)
    prev.add_argument("--sheet", type=int, default=0)
    prev.add_argument("--rows", type=int, default=26)
    extr = sub.add_parser("govinfo-extract", help="Extract monthly yields from verified columns")
    extr.add_argument("--input", type=Path, required=True)
    extr.add_argument("--output", type=Path, required=True)
    extr.add_argument("--source-url", required=True)
    extr.add_argument("--published-on", required=True, help="Real public date, not issue's first day")
    extr.add_argument("--period-col", type=int, required=True, help="0-based spreadsheet column")
    extr.add_argument("--dividend-col", type=int, required=True)
    extr.add_argument("--earnings-col", type=int, required=True)
    extr.add_argument("--sheet", type=int, default=0)
    a = p.parse_args(argv)
    if a.command == "import-prices":
        result = prices_to_file(a.input, a.output)
    elif a.command == "compare-prices":
        result = price_comparison(a.candidate, a.baseline, a.tolerance_bps)
    elif a.command == "govinfo-urls":
        result = govinfo_urls(a.issue, a.page)
    elif a.command == "govinfo-download":
        result = govinfo_download(a.issue, a.page, a.output)
    elif a.command == "govinfo-preview":
        rows = govinfo_preview(a.input, a.sheet, a.rows)
        result = [{"row": i, "cells": {j: c for j, c in enumerate(row) if c}}
                  for i, row in enumerate(rows)]
    else:
        result = govinfo_extract(a)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
