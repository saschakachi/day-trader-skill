#!/usr/bin/env python3
"""Fail-closed offline risk snapshot from a complete paper ledger.

Requires a trusted operator reconciliation. Does not authorize execution.
"""
import datetime
import importlib.util
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("ledger_risk_gate", os.path.join(ROOT, "trader-risk/v1_gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def finite(v):
    x = float(v)
    if not math.isfinite(x):
        raise ValueError("non-finite realized P/L")
    return x

def snapshot(rows, now, reconciled=False, manual_kill_switch=None, cooldown_active=None,
             open_positions=None, pending_orders=None):
    """Use explicit reconciliation and paper-only completed records or refuse."""
    if reconciled is not True or not isinstance(manual_kill_switch, bool) or not isinstance(cooldown_active, bool):
        raise ValueError("explicit operator reconciliation and kill-switch/cooldown states required")
    if open_positions != 0 or pending_orders != 0:
        raise ValueError("no untracked positions or pending orders permitted")
    if not isinstance(rows, list):
        raise ValueError("ledger must be a list")
    today = gate.eastern_time(now).date()
    week_start = today - datetime.timedelta(days=today.weekday())
    daily, weekly, trades, streak = 0.0, 0.0, 0, 0
    ordered = []
    for row in rows:
        if row.get("mode") != "paper" or row.get("actual_r") is None:
            raise ValueError("incomplete or non-paper ledger")
        pnl = finite(row["realized_pnl_usd"])
        r = finite(row["actual_r"])
        if (pnl > 0 and r < 0) or (pnl < 0 and r > 0):
            raise ValueError("P/L and R disagree")
        stamp = datetime.datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("ledger timestamp must include timezone")
        if stamp > now:
            raise ValueError("future ledger timestamp")
        day = gate.eastern_time(stamp).date()
        ordered.append((stamp, day, pnl))
    ordered.sort(key=lambda x: x[0])
    for _, day, pnl in ordered:
        streak = streak + 1 if pnl < 0 else 0
        if day == today:
            trades += 1
            daily += min(0, pnl)
        if week_start <= day <= today:
            weekly += min(0, pnl)
    return {"daily_loss_usd": round(-daily, 2),
            "weekly_loss_usd": round(-weekly, 2),
            "trades_today": trades, "consecutive_losses": streak,
            "kill_switch": manual_kill_switch, "cooldown_active": cooldown_active,
            "source": "reconciled_paper_ledger", "reconciled": True}

def evaluate(ticket, config, rows, now, **reconciliation):
    """Missing/inconsistent ledger state blocks rather than assuming zero losses."""
    try:
        stats = snapshot(rows, now, **reconciliation)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        return {"verdict": "BLOCK", "reasons": ["ledger reconciliation failed: " + str(exc)],
                "paper_only": True}
    return gate.evaluate(ticket, config, stats, now)
