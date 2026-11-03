#!/usr/bin/env python3
"""Append-only JSONL journal for the V1 paper-trading assistant."""
import argparse
import datetime
import json
import os
import math

FIELDS = (
    "ticker", "setup", "timestamp", "market_regime", "catalyst", "entry", "stop",
    "target", "position_size", "expected_r", "historical_expectancy", "actual_exit",
    "actual_r", "realized_pnl_usd", "mae", "mfe", "slippage", "result", "rule_violations", "chart_data",
)


def valid_number(value, name):
    try:
        v = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("%s must be numeric" % name)
    if not math.isfinite(v):
        raise ValueError("%s must be finite" % name)
    return v


def normalize(record):
    out = {key: record.get(key) for key in FIELDS}
    out["timestamp"] = out["timestamp"] or datetime.datetime.now(datetime.timezone.utc).isoformat()
    out["mode"] = "paper"
    fields = ("entry", "stop", "actual_exit", "position_size")
    if all(out[k] is not None for k in fields):
        entry, stop, exit_price = (valid_number(out[k], k) for k in fields[:3])
        qty_value = valid_number(out["position_size"], "position_size")
        if not (0 < stop < entry and exit_price > 0 and qty_value > 0
                and qty_value.is_integer()):
            raise ValueError("invalid closed long trade prices or quantity")
        qty = int(qty_value)
        realized = round((exit_price - entry) * qty, 2)
        actual_r = round((exit_price - entry) / (entry - stop), 4)
        if out["realized_pnl_usd"] is not None:
            if abs(valid_number(out["realized_pnl_usd"], "realized_pnl_usd") - realized) > 0.011:
                raise ValueError("realized P/L does not match prices and quantity")
        if out["actual_r"] is not None:
            if abs(valid_number(out["actual_r"], "actual_r") - actual_r) > 0.00011:
                raise ValueError("actual R does not match entry/stop/exit")
        out["realized_pnl_usd"] = realized
        out["actual_r"] = actual_r
    elif out["realized_pnl_usd"] is not None:
        raise ValueError("realized P/L requires a complete closed trade")
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
