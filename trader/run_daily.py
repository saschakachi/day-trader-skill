#!/usr/bin/env python3
"""One-command, read-only ORB scan and reconciled paper report.

External Yahoo requests occur only when explicitly invoked. No orders.
"""
import argparse
import datetime
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(__file__))

def load_daily():
    spec = importlib.util.spec_from_file_location("one_command_daily", os.path.join(ROOT, "trader", "daily_report.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def build_report(source, config, ledger, reconciliation, now):
    daily = load_daily()
    reasons = daily.scan_validator.validate(source, now)
    hits = source.get("hits", []) if isinstance(source, dict) else []
    if not isinstance(hits, list):
        hits = []
    result = daily.report(hits, config, {}, now, ledger_rows=ledger,
                          reconciliation=reconciliation, require_ledger=True,
                          scan_reasons=reasons)
    result["scan_preflight"] = {"passed": not reasons, "reasons": reasons}
    result["market_data_verified"] = False
    return result

def main(argv=None):
    parser = argparse.ArgumentParser(description="Run ORB scanner and read-only paper report")
    parser.add_argument("--symbols", required=True, help="Comma-separated tickers")
    parser.add_argument("--ledger", required=True, help="Complete paper journal JSONL")
    parser.add_argument("--reconciliation", required=True, help="Operator reconciliation JSON")
    parser.add_argument("--config", default="trader/config.json")
    parser.add_argument("--max-confirm", type=int, default=0, help="0 checks all scanner candidates")
    args = parser.parse_args(argv)
    if args.max_confirm != 0:
        parser.error("full confirmation is required; use --max-confirm 0")
    symbols = args.symbols.split(",")
    if not symbols or any(not s.strip() or not s.strip().replace(".", "").isalpha() for s in symbols):
        parser.error("symbols must be a comma-separated list of tickers")
    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)
    if config.get("mode") != "paper" or config.get("live_trading_enabled") is not False:
        parser.error("paper-only configuration required")
    with open(args.ledger, encoding="utf-8") as f:
        ledger = [json.loads(line) for line in f if line.strip()]
    with open(args.reconciliation, encoding="utf-8") as f:
        reconciliation = json.load(f)
    # Check reconciliation before making any network request.
    now = datetime.datetime.now(datetime.timezone.utc)
    daily = load_daily()
    daily.ledger_risk.snapshot(ledger, now, **reconciliation)
    with tempfile.TemporaryDirectory() as folder:
        out = os.path.join(folder, "scan.json")
        command = [sys.executable, os.path.join(ROOT, "trader-scanner", "scan.py"),
                   "orb", "--symbols", args.symbols, "--max-confirm", "0",
                   "--config", args.config, "--out", out, "--quiet"]
        proc = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, universal_newlines=True,
                              timeout=180)
        if proc.returncode not in (0, 1) or not os.path.isfile(out):
            raise RuntimeError("scanner failed or produced no scan document: " + proc.stderr[-500:])
        with open(out, encoding="utf-8") as f:
            source = json.load(f)
    result = build_report(source, config, ledger, reconciliation,
                          datetime.datetime.now(datetime.timezone.utc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["scan_preflight"]["passed"] else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("Paper workflow BLOCK: " + str(exc), file=sys.stderr)
        sys.exit(2)
