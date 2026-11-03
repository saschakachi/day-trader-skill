import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("evidence_report", os.path.join(ROOT, "trader/daily_report.py"))
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)

class EvidenceRankingTests(unittest.TestCase):
    def setUp(self):
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
                       "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
                       "account_equity_usd": 25000, "max_loss_per_trade_usd": 125,
                       "max_position_pct": 20}
        self.now = datetime.datetime(2026, 10, 19, 10)
        self.hits = [{"ticker": symbol, "setup": "orb", "entry": 100,
                      "stop": 99, "target": 102, "bar_closed": True}
                     for symbol in ("AAA", "BBB")]

    def test_evidence_summary_and_ranking(self):
        evidence = {"BBB": {"orb": [{"r": 1, "outcome": "target_first"} for _ in range(30)]}}
        result = daily.report(self.hits, self.config, {}, self.now, evidence)
        self.assertEqual([x["ticker"] for x in result["candidates"]], ["BBB", "AAA"])
        self.assertEqual(result["candidates"][0]["historical_evidence"]["sample_size"], 30)
        self.assertEqual(result["execution"], "disabled")

    def test_different_setup_is_not_pooled(self):
        evidence = {"AAA": {"20_day_breakout": [{"r": 1} for _ in range(50)]}}
        result = daily.report(self.hits, self.config, {}, self.now, evidence)
        self.assertEqual(result["candidates"][0]["historical_evidence"]["status"], "not_provided")

    def test_small_sample_is_not_promoted(self):
        evidence = {"BBB": {"orb": [{"r": 1} for _ in range(5)]}}
        result = daily.report(self.hits, self.config, {}, self.now, evidence)
        self.assertEqual(result["candidates"][0]["ticker"], "AAA")

    def test_invalid_evidence_cannot_be_promoted(self):
        evidence = {"BBB": {"orb": [{"r": float("nan")} for _ in range(30)]}}
        result = daily.report(self.hits, self.config, {}, self.now, evidence)
        self.assertEqual(result["candidates"][1]["historical_evidence"]["status"], "invalid_evidence")

if __name__ == "__main__":
    unittest.main()
