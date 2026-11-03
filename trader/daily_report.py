#!/usr/bin/env python3
"""Read-only paper candidate report from explicit scanner hits. No orders or network."""
import argparse
import datetime
import importlib.util
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(__file__))

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

risk = load_module("report_risk", "trader-risk/v1_gate.py")
sizing = load_module("report_sizing", "trader-budget/v1_size.py")

def finite(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("price must be finite")
    return result

def normalize_scanner_hit(hit, config=None):
    """Translate scanner schema conservatively; never invent a target or closed-bar flag."""
    if "setup" in hit:
        return hit
    setups = hit.get("setups") or []
    result = dict(hit)
    result["setup"] = setups[0] if len(setups) == 1 else None
    if result["setup"] == "orb":
        result["entry"] = hit.get("price")
        result["stop"] = hit.get("or_low")
        # ORB scanner only confirms a completed breakout bar, not a target.
        result["bar_closed"] = bool(hit.get("at") and hit.get("bar_start"))
        # Opt-in mechanical 2R plan, not an evidence-based price forecast.
        if config and config.get("orb_target_policy") == "fixed_2r":
            try:
                entry, stop = finite(result["entry"]), finite(result["stop"])
                if 0 < stop < entry:
                    result["target"] = round(entry + 2 * (entry - stop), 4)
            except (TypeError, ValueError, KeyError):
                pass
    return result


def report(hits, config, stats, now, evidence=None):
    if not isinstance(hits, list) or not isinstance(stats, dict):
        raise ValueError("hits must be a list and stats must be a dictionary")
    evidence = evidence or {}
    candidates = []
    for raw_hit in hits:
        hit = normalize_scanner_hit(raw_hit, config)
        symbol = str(hit.get("symbol") or hit.get("ticker") or "").upper()
        item = {"ticker": symbol, "setup": hit.get("setup"), "status": "BLOCK",
                "reasons": [], "approval_required": True}
        try:
            if not symbol or not symbol.replace(".", "").isalpha():
                raise ValueError("invalid ticker")
            entry, stop, target = (finite(hit[k]) for k in ("entry", "stop", "target"))
            if not 0 < stop < entry < target:
                raise ValueError("invalid long price levels")
            qty = sizing.size(entry, stop, config["account_equity_usd"],
                              config["max_loss_per_trade_usd"],
                              config["max_position_pct"])["qty"]
            if qty < 1:
                raise ValueError("position size is zero")
            ticket = {"ticker": symbol, "side": "buy", "setup": hit.get("setup"),
                      "bar_closed": hit.get("bar_closed") is True, "entry": entry,
                      "stop": stop, "target": target, "position_size": qty}
            decision = risk.evaluate(ticket, config, stats, now)
            item.update({"entry": entry, "stop": stop, "target": target,
                         "position_size": qty, "max_planned_loss_usd": round(qty * (entry-stop), 2),
                         "reward_risk": round((target-entry)/(entry-stop), 3),
                         "status": decision["verdict"], "reasons": decision["reasons"],
                         "ticket_fingerprint": decision["ticket_fingerprint"],
                         "historical_evidence": evidence.get(symbol, {"status": "not_provided"}),
                         "catalyst": hit.get("catalyst") or "not_provided"})
        except (KeyError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
            item["reasons"].append(str(exc))
        candidates.append(item)
    candidates.sort(key=lambda x: (x["status"] != "PASS", -x.get("reward_risk", 0), x["ticker"]))
    return {"mode": "paper", "execution": "disabled", "as_of": now.isoformat(),
            "passed": sum(c["status"] == "PASS" for c in candidates),
            "candidates": candidates,
            "note": "Review only. PASS is not permission to execute. Missing evidence/catalysts are disclosed."}

def main():
    p = argparse.ArgumentParser(description="Read-only paper candidate report")
    p.add_argument("--hits", required=True, help="JSON list or scanner JSON with hits")
    p.add_argument("--config", default="trader/config.json")
    p.add_argument("--stats", required=True, help="Explicit session statistics JSON")
    p.add_argument("--evidence", help="Optional per-symbol evidence JSON")
    p.add_argument("--now", help="ISO datetime; naive times interpreted as New York wall clock")
    args = p.parse_args()
    with open(args.hits, encoding="utf-8") as f:
        source = json.load(f)
    hits = source.get("hits", []) if isinstance(source, dict) else source
    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)
    with open(args.stats, encoding="utf-8") as f:
        stats = json.load(f)
    evidence = {}
    if args.evidence:
        with open(args.evidence, encoding="utf-8") as f:
            evidence = json.load(f)
    now = datetime.datetime.fromisoformat(args.now) if args.now else datetime.datetime.now(datetime.timezone.utc)
    print(json.dumps(report(hits, config, stats, now, evidence), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
