#!/usr/bin/env python3
"""Run deterministic offline demo and assert risk outcomes. No external I/O."""
import datetime
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(__file__))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

daily = load("demo_daily", "trader/daily_report.py")

def run():
    demo = os.path.join(ROOT, "trader", "demo")
    with open(os.path.join(demo, "scan_hits.json"), encoding="utf-8") as f:
        hits = json.load(f)["hits"]
    with open(os.path.join(demo, "reconciliation.json"), encoding="utf-8") as f:
        reconciliation = json.load(f)
    with open(os.path.join(ROOT, "trader", "config.json"), encoding="utf-8") as f:
        config = json.load(f)
    now = datetime.datetime(2026, 10, 19, 14, 0, tzinfo=datetime.timezone.utc)
    result = daily.report(hits, config, {}, now, ledger_rows=[],
                          reconciliation=reconciliation, require_ledger=True)
    if result["passed"] != 1 or len(result["candidates"]) != 2:
        raise AssertionError("offline demo expected one PASS and one BLOCK")
    if result["execution"] != "disabled":
        raise AssertionError("execution must remain disabled")
    return result

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
