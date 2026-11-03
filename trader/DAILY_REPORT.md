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
