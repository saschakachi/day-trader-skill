import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("local_dashboard", os.path.join(ROOT, "trader/dashboard.py"))
dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard)

class DashboardTests(unittest.TestCase):
    def test_empty_page_has_no_external_dependencies(self):
        page = dashboard.render()
        self.assertIn("Simulierten Handelstag starten", page)
        self.assertIn("PAPER ONLY", page)
        self.assertNotIn("https://", page)
        self.assertNotIn("<script", page)

    def test_demo_result_shows_pass_and_block(self):
        result = dashboard.run()
        page = dashboard.render(result)
        self.assertIn("DEMO", page)
        self.assertIn("PASS", page)
        self.assertIn("BLOCK", page)
        self.assertIn("Deaktiviert", page)

    def test_escape_untrusted_text(self):
        page = dashboard.render({"passed": 0, "candidates": [
            {"ticker": "<script>alert(1)</script>", "status": "BLOCK", "reasons": ["<b>unsafe</b>"]}
        ]})
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("&lt;b&gt;", page)

if __name__ == "__main__":
    unittest.main()
