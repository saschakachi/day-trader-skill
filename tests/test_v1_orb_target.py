import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("orb_report", os.path.join(ROOT, "trader/daily_report.py"))
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)

class OrbTargetTests(unittest.TestCase):
    def setUp(self):
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
                       "account_equity_usd": 25000, "max_loss_per_trade_usd": 125,
                       "max_position_pct": 20, "orb_target_policy": "fixed_2r"}
        self.now = datetime.datetime(2026, 10, 19, 10)
        self.hit = {"symbol": "DEMO", "setups": ["orb"], "price": 100,
                    "or_high": 99, "or_low": 98, "at": "09:50", "bar_start": "09:45"}

    def test_2r_target_and_risk_gate(self):
        result = daily.report([self.hit], self.config, {}, self.now)
        candidate = result["candidates"][0]
        self.assertEqual(candidate["status"], "PASS")
        self.assertEqual(candidate["target"], 104)
        self.assertEqual(candidate["reward_risk"], 2)
        self.assertEqual(candidate["position_size"], 50)
        self.assertEqual(candidate["max_planned_loss_usd"], 100)
        self.assertEqual(result["execution"], "disabled")

    def test_policy_absent_remains_blocked(self):
        config = dict(self.config)
        del config["orb_target_policy"]
        self.assertEqual(daily.report([self.hit], config, {}, self.now)["passed"], 0)

    def test_unconfirmed_bar_remains_blocked(self):
        hit = dict(self.hit)
        del hit["at"]
        self.assertEqual(daily.report([hit], self.config, {}, self.now)["passed"], 0)

    def test_invalid_stop_remains_blocked(self):
        hit = dict(self.hit, or_low=101)
        self.assertEqual(daily.report([hit], self.config, {}, self.now)["passed"], 0)

    def test_weekend_remains_blocked(self):
        self.assertEqual(daily.report([self.hit], self.config, {},
                                      datetime.datetime(2026, 10, 18, 10))["passed"], 0)

if __name__ == "__main__":
    unittest.main()
