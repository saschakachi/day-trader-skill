#!/usr/bin/env python3
"""Append-only JSONL journal for the V1 paper-trading assistant."""
import argparse
import datetime
import json
import os

FIELDS = (
    "ticker", "setup", "timestamp", "market_regime", "catalyst", "entry", "stop",
    "target", "position_size", "expected_r", "historical_expectancy", "actual_exit",
    "actual_r", "mae", "mfe", "slippage", "result", "rule_violations", "chart_data",
)


def normalize(record):
    out = {key: record.get(key) for key in FIELDS}
    out["timestamp"] = out["timestamp"] or datetime.datetime.now(datetime.timezone.utc).isoformat()
    out["mode"] = "paper"
    return out


def append(record, path="trader/journal.jsonl"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    row = normalize(record)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
    return row


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="JSON trade record")
    p.add_argument("--path", default="trader/journal.jsonl")
    args = p.parse_args()
    with open(args.input, encoding="utf-8") as f:
        record = json.load(f)
    print(json.dumps(append(record, args.path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
