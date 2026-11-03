#!/usr/bin/env python3
"""Conservative offline validation of scanner metadata before manual review."""
import datetime
import json
import sys

def validate(doc, now):
    reasons = []
    if not isinstance(doc, dict):
        return ["scanner output must be a JSON object"]
    if doc.get("created_by") != "trader-scanner":
        reasons.append("unverified scanner producer")
    if doc.get("mode") != "orb":
        reasons.append("not a confirmed ORB scan")
    if doc.get("offline") is not None:
        reasons.append("offline fixture is not live market data")
    if doc.get("source") != "yahoo":
        reasons.append("unexpected market data source")
    if not isinstance(doc.get("hits"), list):
        reasons.append("missing hits list")
    try:
        created = datetime.datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
        if created.tzinfo is None or created.utcoffset() is None:
            raise ValueError("timezone required")
        age = (now - created).total_seconds()
        if age < 0 or age > 900:
            reasons.append("scanner data older than 15 minutes or future-dated")
    except (KeyError, TypeError, ValueError, OverflowError):
        reasons.append("invalid scanner timestamp")
    try:
        if int(doc["failed"]) != 0 or int(doc["unconfirmed"]) != 0:
            reasons.append("partial or unconfirmed scan")
        if int(doc["scanned"]) < 1 or int(doc["universe"]) < 1:
            reasons.append("empty scanner coverage")
    except (KeyError, TypeError, ValueError, OverflowError):
        reasons.append("invalid scan coverage metadata")
    return reasons

def main():
    if len(sys.argv) != 2:
        print("Usage: python trader/scan_validation.py trader/watchlist.json", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        doc = json.load(f)
    reasons = validate(doc, datetime.datetime.now(datetime.timezone.utc))
    print(json.dumps({"review_ready": not reasons, "reasons": reasons,
                      "execution": "disabled", "market_data_verified": False}, indent=2))
    return 1 if reasons else 0

if __name__ == "__main__":
    sys.exit(main())
