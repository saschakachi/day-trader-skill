"""Fail-closed regression tests for the V1 paper execution boundary."""
import datetime
import importlib.util
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

risk = load("risk_final", "trader-risk/v1_gate.py")
paper = load("paper_final", "trader-broker/paper_execute.py")
CONFIG = {
    "mode": "paper", "paper": True, "live_trading_enabled": False,
    "risk_gate_bypass": False, "allow_short": False, "allow_margin": False,
    "allow_options": False, "setups": ["orb"], "closed_bars_only": True,
    "min_reward_risk": 1.5, "max_loss_per_trade_usd": 125,
    "account_equity_usd": 25000, "max_position_pct": 20,
    "max_daily_loss_usd": 375, "max_weekly_loss_pct": 4,
    "max_trades_per_day": 4, "max_consecutive_losses": 3,
    "no_entries_before": "09:35", "no_entries_after": "15:30",
}
NOW = datetime.datetime(2026, 10, 19, 10, 0)

class FinalPaperBoundary(unittest.TestCase):
    def ticket(self):
        return {"side": "buy", "setup": "orb", "bar_closed": True,
                "entry": 100, "stop": 99, "target": 102, "position_size": 50}

    def check(self, ticket=None, config=None, stats=None, now=NOW):
        return risk.evaluate(ticket or self.ticket(), config or CONFIG, stats or {}, now)

    def test_valid_paper_ticket_passes(self):
        self.assertEqual(self.check()["verdict"], "PASS")

    def test_live_mode_is_blocked(self):
        config = dict(CONFIG, mode="live", paper=False, live_trading_enabled=True)
        self.assertEqual(self.check(config=config)["verdict"], "BLOCK")

    def test_short_is_blocked(self):
        ticket = self.ticket()
        ticket["side"] = "sell"
        self.assertEqual(self.check(ticket=ticket)["verdict"], "BLOCK")

    def test_unclosed_bar_is_blocked(self):
        ticket = self.ticket()
        ticket["bar_closed"] = False
        self.assertEqual(self.check(ticket=ticket)["verdict"], "BLOCK")

    def test_loss_limit_is_blocked(self):
        ticket = self.ticket()
        ticket["position_size"] = 126
        self.assertEqual(self.check(ticket=ticket)["verdict"], "BLOCK")

    def test_position_limit_is_blocked(self):
        ticket = self.ticket()
        ticket["entry"] = 200
        ticket["stop"] = 199.5
        ticket["target"] = 201
        self.assertEqual(self.check(ticket=ticket)["verdict"], "BLOCK")

    def test_kill_switch_is_blocked(self):
        self.assertEqual(self.check(stats={"kill_switch": True})["verdict"], "BLOCK")

    def test_missing_config_cannot_execute(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                paper.execute(self.ticket(), self.check(), True,
                              os.path.join(d, "orders.json"))
            self.assertFalse(os.path.exists(os.path.join(d, "orders.json")))

    def test_rejected_approval_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "orders.json")
            with self.assertRaises(ValueError):
                paper.execute(self.ticket(), self.check(), False, path, CONFIG)
            self.assertFalse(os.path.exists(path))

    def test_risk_fingerprint_binds_exact_ticket(self):
        ticket = self.ticket()
        result = self.check(ticket=ticket)
        ticket["target"] = 103
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                paper.execute(ticket, result, True, os.path.join(d, "orders.json"), CONFIG)

    def test_simulated_execution_writes_paper_only(self):
        ticket = self.ticket()
        with tempfile.TemporaryDirectory() as d:
            order = paper.execute(ticket, self.check(ticket=ticket), True,
                                  os.path.join(d, "orders.json"), CONFIG)
            self.assertEqual(order["mode"], "paper")
            self.assertEqual(order["status"], "simulated")

if __name__ == "__main__":
    unittest.main()
