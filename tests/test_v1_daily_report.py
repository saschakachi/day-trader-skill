import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("daily_report", os.path.join(ROOT, "trader/daily_report.py"))
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)

class DailyReportTests(unittest.TestCase):
    def setUp(self):
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
                       "account_equity_usd": 25000, "max_loss_per_trade_usd": 125,
                       "max_position_pct": 20}
        self.now = datetime.datetime(2026, 10, 19, 10, 0)
        self.good = {"symbol": "TEST", "setup": "orb", "entry": 100, "stop": 99,
                     "target": 102, "bar_closed": True}

    def test_valid_candidate_is_review_only(self):
        result = daily.report([self.good], self.config, {}, self.now)
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["execution"], "disabled")
        self.assertTrue(result["candidates"][0]["approval_required"])
        self.assertEqual(result["candidates"][0]["position_size"], 50)
        self.assertEqual(result["candidates"][0]["max_planned_loss_usd"], 50)
        self.assertEqual(result["candidates"][0]["historical_evidence"]["status"], "not_provided")

    def test_unclosed_bar_is_blocked(self):
        hit = dict(self.good, bar_closed=False)
        self.assertEqual(daily.report([hit], self.config, {}, self.now)["passed"], 0)

    def test_missing_stop_is_blocked(self):
        hit = dict(self.good)
        del hit["stop"]
        result = daily.report([hit], self.config, {}, self.now)
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["candidates"][0]["status"], "BLOCK")

    def test_weekend_is_blocked(self):
        result = daily.report([self.good], self.config, {}, datetime.datetime(2026, 10, 18, 10))
        self.assertEqual(result["passed"], 0)

    def test_nonfinite_prices_are_blocked(self):
        hit = dict(self.good, entry=float("nan"))
        self.assertEqual(daily.report([hit], self.config, {}, self.now)["passed"], 0)

    def test_sorted_pass_before_block(self):
        hits = [dict(self.good, symbol="BAD", bar_closed=False), self.good]
        result = daily.report(hits, self.config, {}, self.now)
        self.assertEqual([x["ticker"] for x in result["candidates"]], ["TEST", "BAD"])

if __name__ == "__main__":
    unittest.main()
