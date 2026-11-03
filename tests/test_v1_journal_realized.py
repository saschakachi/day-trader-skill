import datetime
import importlib.util
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

journal = load("journal_realized", "trader-journal/journal.py")
stats = load("stats_realized", "trader/paper_stats.py")

class JournalRealizedTests(unittest.TestCase):
    def setUp(self):
        self.trade = {"ticker": "TEST", "setup": "orb", "entry": 100,
                      "stop": 99, "target": 102, "position_size": 50,
                      "actual_exit": 102, "timestamp": "2026-10-19T10:00:00"}

    def test_closed_trade_flows_to_performance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "journal.jsonl")
            saved = journal.append(self.trade, path)
            self.assertEqual(saved["realized_pnl_usd"], 100)
            self.assertEqual(saved["actual_r"], 2)
            with open(path, encoding="utf-8") as f:
                rows = [json.loads(line) for line in f]
            summary = stats.summarize(rows, datetime.date(2026, 10, 19))
            self.assertEqual(summary["total_realized_pnl_usd"], 100)
            self.assertEqual(summary["completed_trades"], 1)

    def test_loss_is_negative(self):
        trade = dict(self.trade, actual_exit=98.5)
        result = journal.normalize(trade)
        self.assertEqual(result["realized_pnl_usd"], -75)
        self.assertEqual(result["actual_r"], -1.5)

    def test_inconsistent_r_rejected(self):
        with self.assertRaises(ValueError):
            journal.normalize(dict(self.trade, actual_r=-1))

    def test_inconsistent_pnl_rejected(self):
        with self.assertRaises(ValueError):
            journal.normalize(dict(self.trade, realized_pnl_usd=500))

    def test_nonfinite_price_rejected(self):
        with self.assertRaises(ValueError):
            journal.normalize(dict(self.trade, actual_exit=float("nan")))

    def test_incomplete_record_cannot_claim_realized_pnl(self):
        trade = dict(self.trade)
        del trade["actual_exit"]
        with self.assertRaises(ValueError):
            journal.normalize(dict(trade, realized_pnl_usd=100))

if __name__ == "__main__":
    unittest.main()
