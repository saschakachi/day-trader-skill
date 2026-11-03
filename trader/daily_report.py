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
evidence_engine = load_module("report_evidence", "trader-timemachine/v1_evidence.py")
ledger_risk = load_module("report_ledger_risk", "trader/risk_from_ledger.py")
scan_validator = load_module("report_scan_validator", "trader/scan_validation.py")

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


def evidence_for(symbol, setup, evidence):
    """Evidence must match the specific ticker/setup; no cross-setup pooling."""
    rows = evidence.get(symbol, {}).get(setup, []) if isinstance(evidence, dict) else []
    if not isinstance(rows, list):
        return {"status": "invalid_evidence"}
    if not rows:
        return {"status": "not_provided", "sample_size": 0}
    try:
        if not all(math.isfinite(float(x["r"])) for x in rows):
            raise ValueError("non-finite R")
        summary = evidence_engine.summarize(rows)
        return summary
    except (KeyError, TypeError, ValueError, OverflowError):
        return {"status": "invalid_evidence"}


def report(hits, config, stats, now, evidence=None, ledger_rows=None, reconciliation=None, require_ledger=False, scan_reasons=None):
    if not isinstance(hits, list) or not isinstance(stats, dict):
        raise ValueError("hits must be a list and stats must be a dictionary")
    evidence = evidence or {}
    try:
        if ledger_rows is None:
            raise ValueError("reconciled paper ledger required")
        verified_stats = ledger_risk.snapshot(ledger_rows, now, **(reconciliation or {}))
        ledger_error = None
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        verified_stats = None
        ledger_error = "ledger reconciliation failed: " + str(exc)
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
            if scan_reasons:
                decision = {"verdict": "BLOCK", "reasons": list(scan_reasons),
                            "ticket_fingerprint": None}
            elif verified_stats is None and require_ledger:
                decision = {"verdict": "BLOCK", "reasons": [ledger_error],
                            "ticket_fingerprint": None}
            else:
                decision = risk.evaluate(ticket, config, verified_stats if verified_stats is not None else stats, now)
            item.update({"entry": entry, "stop": stop, "target": target,
                         "position_size": qty, "max_planned_loss_usd": round(qty * (entry-stop), 2),
                         "reward_risk": round((target-entry)/(entry-stop), 3),
                         "status": decision["verdict"], "reasons": decision["reasons"],
                         "ticket_fingerprint": decision["ticket_fingerprint"],
                         "historical_evidence": evidence_for(symbol, hit.get("setup"), evidence),
                         "catalyst": hit.get("catalyst") or "not_provided"})
        except (KeyError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
            item["reasons"].append(str(exc))
        candidates.append(item)
    # Verified samples rank above unverified ones; evidence is descriptive only.
    def rank(item):
        ev = item.get("historical_evidence") or {}
        supported = ev.get("status") == "historical_evidence_only" and ev.get("sample_size", 0) >= 30
        lower = ev.get("confidence_interval_95_avg_r", [0])[0] if supported else float("-inf")
        return (item["status"] != "PASS", not supported, -lower,
                -item.get("reward_risk", 0), item["ticker"])
    candidates.sort(key=rank)
    return {"mode": "paper", "execution": "disabled", "as_of": now.isoformat(),
            "passed": sum(c["status"] == "PASS" for c in candidates),
            "candidates": candidates,
            "note": "Review only. PASS is not permission to execute. Missing evidence/catalysts are disclosed."}

def main():
    p = argparse.ArgumentParser(description="Read-only paper candidate report")
    p.add_argument("--hits", required=True, help="JSON list or scanner JSON with hits")
    p.add_argument("--config", default="trader/config.json")
    p.add_argument("--stats", help="Legacy statistics JSON (not trusted for PASS)")
    p.add_argument("--ledger", help="Completed paper journal JSONL")
    p.add_argument("--reconciliation", help="Operator reconciliation JSON")
    p.add_argument("--evidence", help="Optional per-symbol evidence JSON")
    p.add_argument("--now", help="ISO datetime; naive times interpreted as New York wall clock")
    args = p.parse_args()
    with open(args.hits, encoding="utf-8") as f:
        source = json.load(f)
    hits = source.get("hits", []) if isinstance(source, dict) else source
    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)
    stats = {}
    if args.stats:
        with open(args.stats, encoding="utf-8") as f:
            stats = json.load(f)
    ledger_rows = None
    reconciliation = None
    if args.ledger:
        with open(args.ledger, encoding="utf-8") as f:
            ledger_rows = [json.loads(line) for line in f if line.strip()]
    if args.reconciliation:
        with open(args.reconciliation, encoding="utf-8") as f:
            reconciliation = json.load(f)
    evidence = {}
    if args.evidence:
        with open(args.evidence, encoding="utf-8") as f:
            evidence = json.load(f)
    now = datetime.datetime.fromisoformat(args.now) if args.now else datetime.datetime.now(datetime.timezone.utc)
    scan_reasons = scan_validator.validate(source, now)
    print(json.dumps(report(hits, config, stats, now, evidence, ledger_rows,
                            reconciliation, True, scan_reasons), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
