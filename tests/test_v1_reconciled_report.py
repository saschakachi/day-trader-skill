import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("report_reconciled", os.path.join(ROOT, "trader/daily_report.py"))
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)

class ReconciledReportTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 10, 19, 15, tzinfo=datetime.timezone.utc)
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
                       "account_equity_usd": 25000, "max_loss_per_trade_usd": 125,
                       "max_position_pct": 20, "max_daily_loss_usd": 375}
        self.hit = {"ticker": "TEST", "setup": "orb", "entry": 100,
                    "stop": 99, "target": 102, "bar_closed": True}
        self.recon = {"reconciled": True, "manual_kill_switch": False,
                      "cooldown_active": False, "open_positions": 0, "pending_orders": 0}

    def test_missing_ledger_blocks(self):
        r = daily.report([self.hit], self.config, {}, self.now, require_ledger=True)
        self.assertEqual(r["passed"], 0)

    def test_complete_reconciliation_passes(self):
        r = daily.report([self.hit], self.config, {}, self.now, ledger_rows=[],
                         reconciliation=self.recon, require_ledger=True)
        self.assertEqual(r["passed"], 1)
        self.assertEqual(r["execution"], "disabled")

    def test_losses_block_even_with_supplied_zero_stats(self):
        row = {"mode": "paper", "timestamp": "2026-10-19T14:00:00+00:00",
               "realized_pnl_usd": -400, "actual_r": -1}
        r = daily.report([self.hit], self.config, {}, self.now, ledger_rows=[row],
                         reconciliation=self.recon, require_ledger=True)
        self.assertEqual(r["passed"], 0)

    def test_incomplete_reconciliation_blocks(self):
        r = daily.report([self.hit], self.config, {}, self.now, ledger_rows=[],
                         reconciliation={"reconciled": True}, require_ledger=True)
        self.assertEqual(r["passed"], 0)

if __name__ == "__main__":
    unittest.main()
