# Daily paper candidate report (read-only)

The report accepts **explicitly supplied** scanner hits and session statistics.
It does not download prices, discover catalysts, approve trades, or place orders.

Example input file `hits.json`:

```json
{"hits":[{"symbol":"DEMO","setup":"orb","entry":100,"stop":99,"target":102,"bar_closed":true,"catalyst":"example only"}]}
```

Example `stats.json` (illustrative; use verified real paper-session counters):

```json
{"daily_loss_usd":0,"weekly_loss_usd":0,"trades_today":0,"consecutive_losses":0,"kill_switch":false,"cooldown_active":false}
```

Run from the repository root:

```sh
python trader/daily_report.py --hits hits.json --stats stats.json --now '2026-10-19T10:00:00-04:00'
```

The output ranks risk-PASS candidates first and includes entry, stop, target,
quantity, reward/risk and planned loss. It also includes BLOCK reasons and
explicitly marks missing historical evidence and catalysts. PASS is a
**review label, not authorization to execute**.

**Scanner compatibility:** the report accepts the scanner's `setups` list. For
ORB hits it maps the reported breakout price to entry and opening-range low to
stop. It does **not** invent a profit target, so raw ORB hits remain BLOCK until
a separately validated target is supplied. Daily close-only hits likewise remain
BLOCK without a complete, confirmed trade plan. Session statistics are supplied by the operator, not yet
computed from a durable trading ledger. Broker integration is absent.

## Mechanical ORB paper target

With `orb_target_policy: fixed_2r` in `trader/config.json`, a scanner ORB hit with a completed breakout bar and a valid opening-range low gets an illustrative **2R** target: `entry + 2 * (entry - stop)`. The existing risk gate still checks the ticket. This target is a rule-based planning assumption, **not** a forecast, proof of profitability, or permission to place an order. No broker order is sent. Incomplete bars or invalid prices remain BLOCK. The policy can be disabled by removing the setting.

## Historical evidence (optional)

Supply `--evidence evidence.json` with outcomes keyed by **ticker and setup**:

```json
{"DEMO":{"orb":[{"r":1.5,"mae_r":-0.4,"mfe_r":1.8,"outcome":"target_first"}]}}
```

The report summarizes supplied R-multiples (sample size, average/median R,
win rate, approximate confidence interval, excursions and outcome counts).
At least **30 observations** are required for evidence-based ranking; smaller
samples are displayed but not promoted. No backtest is run automatically and
no out-of-sample provenance is verified. The confidence interval is a simple
normal approximation, not a guarantee. Historical evidence does not override
risk BLOCK, and does not authorize an order.

## Reconciled ledger required for command-line Risk-PASS

The CLI now requires `--ledger completed_paper.jsonl --reconciliation reconciliation.json`
to issue a PASS. `--stats` alone is **not** sufficient. Example reconciliation:

```json
{"reconciled":true,"manual_kill_switch":false,"cooldown_active":false,"open_positions":0,"pending_orders":0}
```

All ledger timestamps must have timezone offsets and the operator must independently
confirm that the ledger is complete. Without reconciliation, the CLI displays BLOCK.
The Python `report(...)` API retains legacy behavior for existing offline tests;
new integrations **must** pass `require_ledger=True`. This is not a broker
reconciliation or a live trading authorization.
