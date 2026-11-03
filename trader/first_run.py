#!/usr/bin/env python3
"""Offline first-run self-test. No network, broker or real session reconciliation."""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))

def run_selftest(python=sys.executable, root=ROOT):
    command = [python, os.path.join(root, "trader", "demo_run.py")]
    proc = subprocess.run(command, cwd=root, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, universal_newlines=True,
                          timeout=30)
    if proc.returncode != 0:
        raise RuntimeError("offline demo failed: " + proc.stderr[-800:])
    result = json.loads(proc.stdout)
    if (result.get("mode") != "paper" or result.get("execution") != "disabled"
            or result.get("passed") != 1 or len(result.get("candidates", [])) != 2):
        raise ValueError("unexpected offline demo results")
    statuses = sorted(x.get("status") for x in result["candidates"])
    if statuses != ["BLOCK", "PASS"]:
        raise ValueError("offline demo safety outcomes differ")
    return {"selftest": "PASS", "mode": "paper", "network_requested": False,
            "orders_created": False, "demo_candidates": 2,
            "risk_pass": 1, "risk_block": 1,
            "note": "Synthetic data only. No real ledger or market prices verified."}

def main():
    parser = argparse.ArgumentParser(description="Offline first-run paper self-test")
    parser.parse_args()
    print(json.dumps(run_selftest(), indent=2, sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("SELFTEST BLOCK: " + str(exc), file=sys.stderr)
        sys.exit(1)
