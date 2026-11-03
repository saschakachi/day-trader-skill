"""Offline end-to-end paper trade lifecycle regression test.

No market feed, broker, real money, or external network calls.
"""
import datetime
import importlib.util
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sizing = load("e2e_size", "trader-budget/v1_size.py")
risk = load("e2e_risk", "trader-risk/v1_gate.py")
paper = load("e2e_paper", "trader-broker/paper_execute.py")
journal = load("e2e_journal", "trader-journal/journal.py")
workflow = load("e2e_workflow", "trader-orchestrator/orchestrator.py")

class PaperLifecycle(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "trader/config.json"), encoding="utf-8") as f:
            self.config = json.load(f)
        self.ticket = {
            "ticker": "TEST", "side": "buy", "setup": "orb",
            "bar_closed": True, "entry": 100.0, "stop": 99.0, "target": 102.0,
        }
        qty = sizing.size(100, 99,
                          equity=self.config["account_equity_usd"],
                          risk_usd=self.config["max_loss_per_trade_usd"],
                          max_position_pct=self.config["max_position_pct"])["qty"]
        self.ticket["position_size"] = qty
        self.now = datetime.datetime(2026, 10, 19, 10, 0)

    def test_approved_trade_to_closed_journal(self):
        verdict = risk.evaluate(self.ticket, self.config, {}, self.now)
        self.assertEqual(verdict["verdict"], "PASS", verdict["reasons"])
        state = {"state": "DISCOVERED", "mode": "paper"}
        for target in ("WATCHING", "TRIGGERED"):
            state = workflow.transition(state, target)
        with self.assertRaises(PermissionError):
            workflow.transition(state, "APPROVED", "PASS", False)
        state = workflow.transition(state, "APPROVED", "PASS", True)
        with tempfile.TemporaryDirectory() as directory:
            orders_path = os.path.join(directory, "orders.json")
            journal_path = os.path.join(directory, "journal.jsonl")
            order = paper.execute(self.ticket, verdict, True, orders_path, self.config)
            self.assertEqual(order["status"], "simulated")
            self.assertEqual(order["mode"], "paper")
            state = workflow.transition(state, "PAPER_OPEN")
            state = workflow.transition(state, "PAPER_CLOSED")
            journal.append({
                "ticker": "TEST", "setup": "orb", "entry": 100,
                "stop": 99, "target": 102, "position_size": self.ticket["position_size"],
                "actual_exit": 102, "actual_r": 2, "result": "win",
                "rule_violations": [],
            }, journal_path)
            state = workflow.transition(state, "JOURNALED")
            self.assertEqual(state["state"], "JOURNALED")
            with open(orders_path, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["mode"], "paper")
            with open(journal_path, encoding="utf-8") as f:
                rows = [json.loads(line) for line in f]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["mode"], "paper")
            self.assertEqual(rows[0]["actual_r"], 2)

    def test_blocked_trade_never_writes_order(self):
        ticket = dict(self.ticket, bar_closed=False)
        verdict = risk.evaluate(ticket, self.config, {}, self.now)
        self.assertEqual(verdict["verdict"], "BLOCK")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "orders.json")
            with self.assertRaises(ValueError):
                paper.execute(ticket, verdict, True, path, self.config)
            self.assertFalse(os.path.exists(path))

if __name__ == "__main__":
    unittest.main()
