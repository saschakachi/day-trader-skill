import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("ledger_risk", os.path.join(ROOT, "trader/risk_from_ledger.py"))
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

class LedgerRiskTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 10, 19, 15, 0, tzinfo=datetime.timezone.utc)
        self.recon = {"reconciled": True, "manual_kill_switch": False,
                      "cooldown_active": False, "open_positions": 0, "pending_orders": 0}
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
                       "account_equity_usd": 25000, "max_loss_per_trade_usd": 125,
                       "max_position_pct": 20, "max_daily_loss_usd": 375}
        self.ticket = {"ticker": "TEST", "side": "buy", "setup": "orb", "bar_closed": True,
                       "entry": 100, "stop": 99, "target": 102, "position_size": 50}
        self.row = {"mode": "paper", "timestamp": "2026-10-19T14:00:00+00:00",
                    "realized_pnl_usd": -400, "actual_r": -1}

    def test_loss_kill_switch(self):
        result = ledger.evaluate(self.ticket, self.config, [self.row], self.now, **self.recon)
        self.assertEqual(result["verdict"], "BLOCK")
        self.assertTrue(any("daily loss" in x for x in result["reasons"]))

    def test_missing_reconciliation_blocks(self):
        self.assertEqual(ledger.evaluate(self.ticket, self.config, [], self.now)["verdict"], "BLOCK")

    def test_missing_row_fields_blocks(self):
        row = dict(self.row)
        del row["realized_pnl_usd"]
        self.assertEqual(ledger.evaluate(self.ticket, self.config, [row], self.now, **self.recon)["verdict"], "BLOCK")

    def test_naive_timestamp_blocks(self):
        row = dict(self.row, timestamp="2026-10-19T10:00:00")
        self.assertEqual(ledger.evaluate(self.ticket, self.config, [row], self.now, **self.recon)["verdict"], "BLOCK")

    def test_pending_order_blocks(self):
        recon = dict(self.recon, pending_orders=1)
        self.assertEqual(ledger.evaluate(self.ticket, self.config, [], self.now, **recon)["verdict"], "BLOCK")

    def test_manual_kill_switch_blocks(self):
        recon = dict(self.recon, manual_kill_switch=True)
        self.assertEqual(ledger.evaluate(self.ticket, self.config, [], self.now, **recon)["verdict"], "BLOCK")

    def test_winning_trade_does_not_erase_prior_loss(self):
        win = dict(self.row, timestamp="2026-10-19T14:30:00+00:00",
                   realized_pnl_usd=500, actual_r=2)
        snapshot = ledger.snapshot([self.row, win], self.now, **self.recon)
        self.assertEqual(snapshot["daily_loss_usd"], 400)

if __name__ == "__main__":
    unittest.main()
