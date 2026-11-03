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

**Limits:** scanner raw hits may not contain the entry/stop/target/setup/closed-bar
fields expected by this report; a validated mapping/strategy confirmation step
is still needed. Session statistics are supplied by the operator, not yet
computed from a durable trading ledger. Broker integration is absent.
