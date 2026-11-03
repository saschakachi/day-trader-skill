import datetime
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("scan_validation", os.path.join(ROOT, "trader/scan_validation.py"))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

class ScanValidationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 10, 19, 14, 0, tzinfo=datetime.timezone.utc)
        self.doc = {"created_by": "trader-scanner", "created_at": "2026-10-19T13:55:00Z",
                    "mode": "orb", "source": "yahoo", "hits": [], "failed": 0,
                    "unconfirmed": 0, "scanned": 5, "universe": 5}

    def test_fresh_complete_scan_is_review_ready(self):
        self.assertEqual(validator.validate(self.doc, self.now), [])

    def test_old_scan_rejected(self):
        doc = dict(self.doc, created_at="2026-10-19T13:00:00Z")
        self.assertTrue(validator.validate(doc, self.now))

    def test_partial_scan_rejected(self):
        self.assertTrue(validator.validate(dict(self.doc, failed=2), self.now))

    def test_offline_fixture_rejected(self):
        self.assertTrue(validator.validate(dict(self.doc, offline="fixture.json"), self.now))

    def test_daily_close_scan_rejected(self):
        self.assertTrue(validator.validate(dict(self.doc, mode="daily"), self.now))

    def test_missing_timestamp_rejected(self):
        doc = dict(self.doc)
        del doc["created_at"]
        self.assertTrue(validator.validate(doc, self.now))

if __name__ == "__main__":
    unittest.main()
