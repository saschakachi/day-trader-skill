#!/usr/bin/env python3
"""Read-only, conservative statistics from completed paper journal records."""
import argparse
import datetime
import json
import math

def number(value, name):
    v = float(value)
    if not math.isfinite(v):
        raise ValueError("%s must be finite" % name)
    return v

def summarize(rows, day):
    """Use only paper rows with complete realized P/L; reject ambiguous data."""
    if not isinstance(rows, list):
        raise ValueError("journal must be a list")
    parsed = []
    for row in rows:
        if row.get("mode") != "paper":
            raise ValueError("non-paper journal entry")
        if row.get("actual_r") is None or row.get("realized_pnl_usd") is None:
            raise ValueError("missing realized R or P/L; incomplete ledger")
        stamp = datetime.datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))
        pnl = number(row["realized_pnl_usd"], "realized_pnl_usd")
        r = number(row["actual_r"], "actual_r")
        parsed.append((stamp, pnl, r))
    parsed.sort(key=lambda x: x[0])
    total = sum(x[1] for x in parsed)
    wins = sum(x[1] > 0 for x in parsed)
    losses = sum(x[1] < 0 for x in parsed)
    consecutive = 0
    for _, pnl, _ in parsed:
        consecutive = consecutive + 1 if pnl < 0 else 0
    today = [x for x in parsed if x[0].date() == day]
    week_start = day - datetime.timedelta(days=day.weekday())
    week = [x for x in parsed if week_start <= x[0].date() <= day]
    return {"mode": "paper", "completed_trades": len(parsed),
            "win_rate": round(wins / len(parsed), 4) if parsed else None,
            "wins": wins, "losses": losses,
            "avg_r": round(sum(x[2] for x in parsed) / len(parsed), 4) if parsed else None,
            "total_realized_pnl_usd": round(total, 2),
            "daily_loss_usd": round(max(0, -sum(x[1] for x in today)), 2),
            "weekly_loss_usd": round(max(0, -sum(x[1] for x in week)), 2),
            "trades_today": len(today), "consecutive_losses": consecutive,
            "kill_switch": False, "cooldown_active": False,
            "warning": "No live positions, pending orders, manual kill switch or exchange timezone reconciled."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--journal", default="trader/journal.jsonl")
    p.add_argument("--date", required=True, help="Trading date YYYY-MM-DD")
    args = p.parse_args()
    with open(args.journal, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    print(json.dumps(summarize(rows, datetime.date.fromisoformat(args.date)), indent=2))

if __name__ == "__main__":
    main()
