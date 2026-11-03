# Checking real-market scanner results before manual review

The scanner already supports unofficial Yahoo Finance price endpoints:

```sh
python trader-scanner/scan.py orb --symbols AAPL,MSFT --out trader/watchlist.json
python trader/scan_validation.py trader/watchlist.json
```

The validator checks the scanner's declared producer, ORB mode, source,
timestamp freshness (15 minutes), full scan coverage and lack of fetch failures.
It rejects offline fixtures as live-market results. Exit status 0 means
**metadata review-ready only**; it does **not** independently authenticate
Yahoo prices, verify exchange trades or authorize any order.

The validator is currently a separate read-only preflight tool. It does not
automatically run the scanner, and is not yet a mandatory condition in the
daily risk report. Market-data feeds may be delayed or incomplete, and
availability depends on external network access. The scanner's 0 exit code
indicates hits, not profitable trades.
