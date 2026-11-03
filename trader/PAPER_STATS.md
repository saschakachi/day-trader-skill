# Paper trade performance summary

The read-only `trader/paper_stats.py` command calculates statistics from
**completed** paper trades with explicit realized USD P/L and R-multiples.

Example journal JSONL line:

```json
{"mode":"paper","timestamp":"2026-10-19T10:00:00","actual_r":1.5,"realized_pnl_usd":75}
```

Run from the repository root:

```sh
python trader/paper_stats.py --journal my_completed_paper_trades.jsonl --date 2026-10-19
```

The report includes completed trades, wins/losses, win rate, average R,
realized P/L, daily/weekly net losses, trades for the selected date and the
current consecutive-loss count. Missing realized values or non-paper rows are
rejected rather than silently counted.

**Important limitations:** This is a reporting tool, **not** a trustworthy
risk-gate stats feed. Dates are taken from the timestamps as supplied (no
New York timezone normalization); daily/weekly losses are net totals and may
understate intraday drawdown. The existing journal writer does not yet supply
`realized_pnl_usd` by default. Manual kill switch, cooldown, open positions,
pending orders and broker fills are not reconciled. Do not pass this output
directly into the risk gate without additional validation.
