import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V1SafetyTests(unittest.TestCase):
    def test_config_locks_paper_only_limits(self):
        config = json.loads((ROOT / "trader/config.json").read_text())
        self.assertTrue(config["paper"])
        self.assertFalse(config["live_trading_enabled"])
        self.assertFalse(config["risk_gate_bypass"])
        self.assertFalse(config["allow_short"])
        self.assertFalse(config["allow_margin"])
        self.assertFalse(config["allow_options"])
        self.assertEqual(config["max_loss_per_trade_usd"], 125)
        self.assertEqual(config["max_daily_loss_usd"], 375)
        self.assertEqual(config["max_trades_per_day"], 4)
        self.assertEqual(config["min_reward_risk"], 1.5)
        self.assertEqual(config["max_position_pct"], 20)

    def test_orchestrator_blocks_approval_without_risk_pass(self):
        o = load("trader-orchestrator/orchestrator.py", "orchestrator")
        with self.assertRaises(PermissionError):
            o.transition({"state": "TRIGGERED"}, "APPROVED", "BLOCK", True)

    def test_orchestrator_blocks_paper_open_without_approval(self):
        o = load("trader-orchestrator/orchestrator.py", "orchestrator2")
        with self.assertRaises(PermissionError):
            o.transition({"state": "APPROVED", "mode": "paper", "risk_verdict": "PASS"}, "PAPER_OPEN")


if __name__ == "__main__":
    unittest.main()
