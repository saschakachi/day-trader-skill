# Deterministic offline paper demo

Run from the repository root:

```sh
python trader/demo_run.py
```

The demo uses fixed, **synthetic** scanner hits and a fixed market date
(Monday 2026-10-19, 10:00 New York time). It expects one risk-PASS ORB
candidate with a mechanical 2R target and one BLOCK due to an invalid stop.

The sample reconciliation file is **fictional** and valid only for this
self-contained demo. Never use it as a real declaration that a trading
ledger, open positions or pending orders have been reconciled.

The demo does not connect to a market data feed, news source, broker or
Trade Republic, and never writes orders. The reported PASS means the
synthetic trade passes the configured paper checks, **not** that it is a
profitable opportunity or ready for live trading.
