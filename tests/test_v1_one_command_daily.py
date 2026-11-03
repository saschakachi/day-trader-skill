import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("one_command_workflow", os.path.join(ROOT, "trader/run_daily.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class OneCommandDailyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 10, 19, 14, tzinfo=datetime.timezone.utc)
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
                       "account_equity_usd": 25000, "max_loss_per_trade_usd": 125,
                       "max_position_pct": 20, "orb_target_policy": "fixed_2r"}
        self.recon = {"reconciled": True, "manual_kill_switch": False,
                      "cooldown_active": False, "open_positions": 0, "pending_orders": 0}
        self.scan = {"created_by": "trader-scanner", "created_at": "2026-10-19T13:55:00Z",
                     "mode": "orb", "source": "yahoo", "failed": 0, "unconfirmed": 0,
                     "scanned": 1, "universe": 1,
                     "hits": [{"symbol": "DEMO", "setups": ["orb"], "price": 100,
                               "or_high": 99, "or_low": 98, "at": "09:50", "bar_start": "09:45"}]}

    def test_complete_scan_and_ledger(self):
        result = runner.build_report(self.scan, self.config, [], self.recon, self.now)
        self.assertTrue(result["scan_preflight"]["passed"])
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["execution"], "disabled")
        self.assertFalse(result["market_data_verified"])

    def test_stale_scan_blocks(self):
        scan = dict(self.scan, created_at="2026-10-19T13:00:00Z")
        result = runner.build_report(scan, self.config, [], self.recon, self.now)
        self.assertEqual(result["passed"], 0)
        self.assertFalse(result["scan_preflight"]["passed"])

    def test_unreconciled_ledger_blocks(self):
        result = runner.build_report(self.scan, self.config, [], {}, self.now)
        self.assertEqual(result["passed"], 0)

    def test_partial_scan_blocks(self):
        result = runner.build_report(dict(self.scan, failed=1),
                                     self.config, [], self.recon, self.now)
        self.assertEqual(result["passed"], 0)

    def test_invalid_price_blocks(self):
        scan = dict(self.scan, hits=[dict(self.scan["hits"][0], or_low=101)])
        result = runner.build_report(scan, self.config, [], self.recon, self.now)
        self.assertEqual(result["passed"], 0)

    def test_no_hits_is_not_a_trade(self):
        scan = dict(self.scan, hits=[])
        result = runner.build_report(scan, self.config, [], self.recon, self.now)
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["candidates"], [])

if __name__ == "__main__":
    unittest.main()
