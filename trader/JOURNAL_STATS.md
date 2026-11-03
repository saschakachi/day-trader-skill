# Closed paper trades: journal to performance report

For a **completed long paper trade**, the journal now computes:
- `realized_pnl_usd = (actual_exit - entry) * position_size`
- `actual_r = (actual_exit - entry) / (entry - stop)`

It checks explicitly supplied values for consistency and rejects invalid
prices, non-integer quantities and non-finite numbers.

Example:

```json
{"ticker":"DEMO","setup":"orb","timestamp":"2026-10-19T10:00:00","entry":100,"stop":99,"target":102,"position_size":50,"actual_exit":102}
```

```sh
python trader-journal/journal.py --input closed_trade.json --path trader/journal.jsonl
python trader/paper_stats.py --journal trader/journal.jsonl --date 2026-10-19
```

The computed P/L excludes commissions, FX costs and slippage unless those
effects are already reflected in the supplied entry/exit prices. The timestamp
must represent the **close time** when used for daily statistics. The journal
remains append-only, and the performance report still is **not** a validated
risk-gate input. Historical rows with missing realized P/L will be rejected by
the report. No real broker or live trading integration exists.
