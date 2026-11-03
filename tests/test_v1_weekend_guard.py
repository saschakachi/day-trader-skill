import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("risk_weekend", os.path.join(ROOT, "trader-risk/v1_gate.py"))
risk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(risk)

class WeekendGuard(unittest.TestCase):
    def test_weekend_blocks_otherwise_valid_paper_ticket(self):
        ticket = {"side": "buy", "setup": "orb", "bar_closed": True,
                  "entry": 100, "stop": 99, "target": 102, "position_size": 50}
        config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                  "risk_gate_bypass": False, "allow_short": False,
                  "allow_margin": False, "allow_options": False,
                  "setups": ["orb"], "closed_bars_only": True,
                  "no_entries_before": "09:35", "no_entries_after": "15:30"}
        for day in (17, 18):
            with self.subTest(day=day):
                result = risk.evaluate(ticket, config, {},
                                       datetime.datetime(2026, 10, day, 10, 0))
                self.assertEqual(result["verdict"], "BLOCK")
                self.assertIn("market closed on weekends", result["reasons"])

if __name__ == "__main__":
    unittest.main()
