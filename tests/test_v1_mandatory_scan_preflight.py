import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("preflight_report", os.path.join(ROOT, "trader/daily_report.py"))
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)

class MandatoryScanPreflightTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 10, 19, 14, tzinfo=datetime.timezone.utc)
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
                       "account_equity_usd": 25000, "max_loss_per_trade_usd": 125,
                       "max_position_pct": 20}
        self.hit = {"ticker": "TEST", "setup": "orb", "entry": 100,
                    "stop": 99, "target": 102, "bar_closed": True}
        self.recon = {"reconciled": True, "manual_kill_switch": False,
                      "cooldown_active": False, "open_positions": 0, "pending_orders": 0}
        self.scan = {"created_by": "trader-scanner", "created_at": "2026-10-19T13:55:00Z",
                     "mode": "orb", "source": "yahoo", "hits": [self.hit],
                     "failed": 0, "unconfirmed": 0, "scanned": 5, "universe": 5}

    def check(self, scan):
        reasons = daily.scan_validator.validate(scan, self.now)
        return daily.report([self.hit], self.config, {}, self.now, ledger_rows=[],
                            reconciliation=self.recon, require_ledger=True,
                            scan_reasons=reasons)

    def test_fresh_complete_scan_passes(self):
        self.assertEqual(self.check(self.scan)["passed"], 1)

    def test_stale_scan_blocks(self):
        scan = dict(self.scan, created_at="2026-10-19T13:00:00Z")
        self.assertEqual(self.check(scan)["passed"], 0)

    def test_partial_scan_blocks(self):
        self.assertEqual(self.check(dict(self.scan, failed=1))["passed"], 0)

    def test_offline_fixture_blocks(self):
        self.assertEqual(self.check(dict(self.scan, offline="fixture.json"))["passed"], 0)

    def test_unreconciled_ledger_blocks_even_fresh_scan(self):
        result = daily.report([self.hit], self.config, {}, self.now,
                              ledger_rows=[], require_ledger=True,
                              scan_reasons=daily.scan_validator.validate(self.scan, self.now))
        self.assertEqual(result["passed"], 0)

if __name__ == "__main__":
    unittest.main()
