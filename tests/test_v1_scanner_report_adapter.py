import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("daily_adapter", os.path.join(ROOT, "trader/daily_report.py"))
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)

class ScannerAdapterTests(unittest.TestCase):
    def setUp(self):
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
                       "account_equity_usd": 25000, "max_loss_per_trade_usd": 125,
                       "max_position_pct": 20}
        self.now = datetime.datetime(2026, 10, 19, 10, 0)

    def test_orb_scanner_hit_missing_target_is_blocked(self):
        hit = {"symbol": "DEMO", "setups": ["orb"], "price": 100, "or_high": 99,
               "or_low": 98, "at": "09:50", "bar_start": "09:45"}
        result = daily.report([hit], self.config, {}, self.now)
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["candidates"][0]["setup"], "orb")
        self.assertEqual(result["candidates"][0]["status"], "BLOCK")
        self.assertIn("target", result["candidates"][0]["reasons"][0])

    def test_daily_close_scanner_hit_not_treated_as_entry(self):
        hit = {"symbol": "DEMO", "setups": ["breakout_20d"], "price": 100,
               "close_date": "2026-10-16"}
        result = daily.report([hit], self.config, {}, self.now)
        self.assertEqual(result["passed"], 0)

    def test_ambiguous_setups_cannot_be_assumed(self):
        hit = {"symbol": "DEMO", "setups": ["orb", "breakout_20d"], "price": 100}
        result = daily.report([hit], self.config, {}, self.now)
        self.assertIsNone(result["candidates"][0]["setup"])
        self.assertEqual(result["passed"], 0)

if __name__ == "__main__":
    unittest.main()
