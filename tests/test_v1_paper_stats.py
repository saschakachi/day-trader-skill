import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("paper_stats", os.path.join(ROOT, "trader/paper_stats.py"))
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)

class PaperStatsTests(unittest.TestCase):
    def setUp(self):
        self.day = datetime.date(2026, 10, 19)
        self.rows = [
            {"mode": "paper", "timestamp": "2026-10-16T10:00:00",
             "actual_r": -1, "realized_pnl_usd": -100},
            {"mode": "paper", "timestamp": "2026-10-19T10:00:00",
             "actual_r": 2, "realized_pnl_usd": 200},
            {"mode": "paper", "timestamp": "2026-10-19T11:00:00",
             "actual_r": -1, "realized_pnl_usd": -100}]

    def test_performance_summary(self):
        result = stats.summarize(self.rows, self.day)
        self.assertEqual(result["completed_trades"], 3)
        self.assertEqual(result["total_realized_pnl_usd"], 0)
        self.assertEqual(result["trades_today"], 2)
        self.assertEqual(result["consecutive_losses"], 1)
        self.assertEqual(result["avg_r"], 0)
        self.assertNotIn("kill_switch", result)

    def test_missing_realized_pnl_rejected(self):
        with self.assertRaises(ValueError):
            stats.summarize([{"mode": "paper", "timestamp": "2026-10-19T10:00:00",
                              "actual_r": 1}], self.day)

    def test_non_paper_row_rejected(self):
        with self.assertRaises(ValueError):
            stats.summarize([dict(self.rows[0], mode="live")], self.day)

    def test_nonfinite_pnl_rejected(self):
        with self.assertRaises(ValueError):
            stats.summarize([dict(self.rows[0], realized_pnl_usd=float("nan"))], self.day)

    def test_empty_ledger_has_no_claimed_win_rate(self):
        result = stats.summarize([], self.day)
        self.assertIsNone(result["win_rate"])
        self.assertEqual(result["completed_trades"], 0)

if __name__ == "__main__":
    unittest.main()
