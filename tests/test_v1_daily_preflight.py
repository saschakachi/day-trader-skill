import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("preflight_runner", os.path.join(ROOT, "trader/run_daily.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class DailyPreflightTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 10, 19, 14, tzinfo=datetime.timezone.utc)
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False}
        self.recon = {"reconciled": True, "manual_kill_switch": False,
                      "cooldown_active": False, "open_positions": 0, "pending_orders": 0}

    def test_safe_empty_ledger_passes(self):
        self.assertEqual(runner.preflight(self.config, [], self.recon, self.now)["trades_today"], 0)

    def test_live_config_rejected(self):
        with self.assertRaises(ValueError):
            runner.preflight(dict(self.config, live_trading_enabled=True), [], self.recon, self.now)

    def test_bypass_rejected(self):
        with self.assertRaises(ValueError):
            runner.preflight(dict(self.config, risk_gate_bypass=True), [], self.recon, self.now)

    def test_missing_reconciliation_rejected(self):
        with self.assertRaises(ValueError):
            runner.preflight(self.config, [], {}, self.now)

    def test_untracked_pending_orders_rejected(self):
        with self.assertRaises(ValueError):
            runner.preflight(self.config, [], dict(self.recon, pending_orders=1), self.now)

    def test_incomplete_journal_rejected(self):
        with self.assertRaises((ValueError, KeyError)):
            runner.preflight(self.config, [{"mode": "paper"}], self.recon, self.now)

if __name__ == "__main__":
    unittest.main()
