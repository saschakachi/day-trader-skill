# Reconciled paper ledger risk check

`trader/risk_from_ledger.py` is a separate **fail-closed** wrapper around
the existing paper-only risk gate. It rejects missing or inconsistent
completed-paper-trade records rather than assuming losses are zero.

The caller must explicitly supply:
- `reconciled=True` after independently checking that the ledger is complete;
- boolean manual kill-switch and cooldown states;
- `open_positions=0` and `pending_orders=0`;
- timezone-aware timestamps on every completed paper trade.

The wrapper counts realized losing trades without offsetting earlier losses
with subsequent winners, applies New York session dates, and passes the
result to the existing risk gate. An incomplete ledger yields BLOCK.

**Not a production risk authority:** reconciliation is an operator assertion,
not cryptographic proof; the wrapper does not itself load the broker, inspect
pending orders, enforce a unique trade ID, or reconstruct intraday account
drawdown. The existing daily report and paper order simulator are not yet
wired to this wrapper. It must not be used to enable real trading.
