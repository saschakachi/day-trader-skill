import importlib.util
import os
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("first_run", os.path.join(ROOT, "trader/first_run.py"))
first = importlib.util.module_from_spec(spec)
spec.loader.exec_module(first)

class FirstRunTests(unittest.TestCase):
    def test_synthetic_demo_selftest(self):
        result = first.run_selftest()
        self.assertEqual(result["selftest"], "PASS")
        self.assertFalse(result["network_requested"])
        self.assertFalse(result["orders_created"])
        self.assertEqual(result["risk_block"], 1)

    def test_failed_subprocess_blocks(self):
        with mock.patch.object(first.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=2, stdout="", stderr="failed")
            with self.assertRaises(RuntimeError):
                first.run_selftest()

    def test_incorrect_safety_outcomes_block(self):
        with mock.patch.object(first.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0,
                stdout='{"mode":"paper","execution":"disabled","passed":2,"candidates":[]}',
                stderr="")
            with self.assertRaises(ValueError):
                first.run_selftest()

if __name__ == "__main__":
    unittest.main()
