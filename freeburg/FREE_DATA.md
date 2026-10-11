# Free-data acquisition and publication audit (2026-10-11)

**Status: prototype; not a cleared one-command reproduction.** Free to access does not imply permission to redistribute or use commercially. Do not publish the existing mixed-origin CSVs unchanged.

| Sleeve | Free alternative | Outstanding |
| --- | --- | --- |
| Primas | Fed H.15 + NBER CP; user-supplied S&P closes | Confirm price source access/rights; replay parity |
| Triple-40 | Fed/NBER + Moody's Baa through H.15/FRED | Moody's third-party rights, price data parity |
| Pu Shen | Extracted FRASER Economic Indicators; GovInfo Excel tables 1995+ | Archived S&P workbook and S&P rights, publication-time validation |
| Competitive | FRASER/GovInfo dividends, official CPI/Treasury | S&P-derived figures, publication-time validation |
| Prime/Discount | Official H.15 historical prime and discount series | Build an alternative from Fed records and compare decisions to frozen reference |
| Heine | Fed yields and archived DJ20/Utilities/CRB digitizations | No exact validated free DJ20 total-return reconstruction |

The original research archive already has FRASER earnings-yield quarterly and dividend-yield weekly first-publication files, plus scripts to acquire and parse old publications. Preserve those costly reconstructions; do not redo archival OCR.

## New user-side utility

`freeburg/tools/free_data.py` accepts **locally obtained** daily/weekly `Date,Close` or `date,spx` files. It never scrapes or redistributes market data.

```bash
python freeburg/tools/free_data.py import-prices --input local/spx.csv --output local/spx_weekly.csv
python freeburg/tools/free_data.py compare-prices --candidate local/spx_weekly.csv --baseline freeburg/prime_discount/data/spx_weekly_2026-08-07.csv
```

The comparator reports overlap, basis-point discrepancies, and changed 52-week S&P-versus-moving-average decisions. The reference CSV is present in the *private* research branch but must be replaced or cleared before publishing.

GovInfo (official Economic Indicators spreadsheets) is a promising 1995+ source. A page is not necessarily the same across monthly issues. After identifying an actual **Common Stock Prices and Yields** granule, inspect first, and only then extract verified columns and publication date:

```bash
python freeburg/tools/free_data.py govinfo-urls --issue 2012-10 --page 31
python freeburg/tools/free_data.py govinfo-download --issue 2012-10 --page 31 --output local/table.xls
pip install pandas xlrd openpyxl
python freeburg/tools/free_data.py govinfo-preview --input local/table.xls
python freeburg/tools/free_data.py govinfo-extract --input local/table.xls --output local/yields.csv --source-url <verified-official-granule-url> --published-on <verified-YYYY-MM-DD> --period-col <N> --dividend-col <N> --earnings-col <N>
```

The date and columns are intentionally required. Outputs are **preliminary extracts**, not verified point-in-time economic events. Direct government table access was not live-tested from the execution environment.

## Rights and source notes

- FRASER calls *Economic Indicators* “No Copyright – United States,” but S&P-derived tables may retain third-party rights. Clear the constituent columns and origins.
- GovInfo's official page: https://www.govinfo.gov/help/econi
- FRASER publication: https://fraser.stlouisfed.org/title/economic-indicators-1
- FRED terms (series-specific third-party restrictions): https://fred.stlouisfed.org/legal/
- Moody's Baa: https://fred.stlouisfed.org/series/BAA
- S&P market prices sourced from Yahoo should not be bundled without permission.
- Stooq offers no-cost manually accessible historical data, **not** automatically redistribution/commercial-use permission; do not scrape it by default.
- Pinnacle is an optional historical comparison, not a required purchase.

## Non-negotiable release gates

1. Audit every column of the current composite historical CSVs for third-party rights.
2. Confirm real GovInfo XLS files, actual table layouts, and real publication dates. Compare to archived FRASER vintage rows.
3. Independently download authorised price data and compare weekly levels and strategy decisions.
4. Add the Fed-only Prime/Discount alternative and compare its 1970–2013 decisions and performance.
5. Heine is **PROXY_UNVERIFIED** until bond history is accurately reconstructed.
6. Ship legally distributable sample data separately from user-supplied historical inputs.

The tools are for reproducible validation, **not** a legal opinion or proof that vendor data may be redistributed.
