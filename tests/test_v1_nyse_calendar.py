import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("nyse_calendar", os.path.join(ROOT, "trader-risk/v1_gate.py"))
risk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(risk)

class NYSECalendar(unittest.TestCase):
    def setUp(self):
        self.ticket = {"side": "buy", "setup": "orb", "bar_closed": True,
                       "entry": 100, "stop": 99, "target": 102, "position_size": 50}
        self.config = {"mode": "paper", "paper": True, "live_trading_enabled": False,
                       "risk_gate_bypass": False, "allow_short": False,
                       "allow_margin": False, "allow_options": False,
                       "setups": ["orb"], "closed_bars_only": True,
                       "no_entries_before": "09:35", "no_entries_after": "15:30"}

    def verdict(self, when):
        return risk.evaluate(self.ticket, self.config, {}, when)["verdict"]

    def test_regular_monday_open(self):
        self.assertEqual(self.verdict(datetime.datetime(2026, 10, 19, 10)), "PASS")

    def test_thanksgiving_closed(self):
        self.assertEqual(self.verdict(datetime.datetime(2026, 11, 26, 10)), "BLOCK")

    def test_good_friday_closed(self):
        self.assertEqual(self.verdict(datetime.datetime(2026, 4, 3, 10)), "BLOCK")

    def test_christmas_observed_closed(self):
        self.assertEqual(self.verdict(datetime.datetime(2027, 12, 24, 10)), "BLOCK")

    def test_thanksgiving_early_close(self):
        self.assertEqual(self.verdict(datetime.datetime(2026, 11, 27, 12, 0)), "PASS")
        self.assertEqual(self.verdict(datetime.datetime(2026, 11, 27, 13, 0)), "BLOCK")

    def test_utc_to_new_york_winter(self):
        utc = datetime.timezone.utc
        self.assertEqual(self.verdict(datetime.datetime(2026, 11, 2, 15, 0, tzinfo=utc)), "PASS")
        self.assertEqual(self.verdict(datetime.datetime(2026, 11, 2, 21, 0, tzinfo=utc)), "BLOCK")

    def test_utc_to_new_york_summer(self):
        utc = datetime.timezone.utc
        self.assertEqual(self.verdict(datetime.datetime(2026, 7, 6, 14, 0, tzinfo=utc)), "PASS")
        self.assertEqual(self.verdict(datetime.datetime(2026, 7, 6, 20, 0, tzinfo=utc)), "BLOCK")

if __name__ == "__main__":
    unittest.main()
