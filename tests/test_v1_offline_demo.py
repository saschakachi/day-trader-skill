import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("offline_demo", os.path.join(ROOT, "trader/demo_run.py"))
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)

class OfflineDemoTests(unittest.TestCase):
    def test_scanner_to_reconciled_report(self):
        result = demo.run()
        self.assertEqual(result["mode"], "paper")
        self.assertEqual(result["execution"], "disabled")
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["candidates"][0]["status"], "PASS")
        self.assertEqual(result["candidates"][0]["target"], 104)
        self.assertEqual(result["candidates"][1]["status"], "BLOCK")

if __name__ == "__main__":
    unittest.main()
