# One-command paper ORB workflow

From the repository root, after installing Python and providing a **real**
completed paper journal and independently verified reconciliation file:

```sh
python trader/run_daily.py --symbols AAPL,MSFT --ledger trader/journal.jsonl --reconciliation reconciliation.json
```

The command checks the paper configuration and operator reconciliation,
fetches the scanner's current Yahoo-based 5-minute ORB data, validates its
metadata, and prints a read-only risk report with PASS/BLOCK reasons.
It requests full confirmation of scanner candidates and does not persist
orders or market data. A scanner result with no hits produces no trade.

The reconciliation file must contain `reconciled`, `manual_kill_switch`,
`cooldown_active`, `open_positions`, and `pending_orders`. The operator
must actually verify these values. Do **not** reuse the synthetic demo
reconciliation as if it described a real paper session.

This script is **manually started**, not scheduled or hosted. Yahoo data is
unofficial and may be delayed. Scanner metadata is self-reported, not
independent price verification. A risk PASS does not mean a profitable setup
or permission to execute. There is no Trade Republic connection.

Important: the scanner uses the current US market session; run it during
the configured entry window, not overnight. The ledger must be complete,
with timezone-aware timestamps and realized outcomes. Missing data blocks
the workflow.

## First run: offline preflight

Before requesting market data, check the paper configuration, completed journal and operator reconciliation:

```sh
python trader/run_daily.py --symbols AAPL,MSFT --ledger trader/journal.jsonl --reconciliation reconciliation.json --check-only
```

This performs **no network request** and places no orders. It returns PASS only if the configuration and supplied reconciliation satisfy the safety checks. A PASS does not independently prove the ledger is complete; the operator remains responsible for that declaration. Remove `--check-only` to run the actual market scanner during US trading hours.
