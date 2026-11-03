#!/usr/bin/env python3
"""Deterministic V1 setup/trigger/confirmation/invalidation builder."""
APPROVED={"orb","20_day_breakout","vwap_ma_reclaim"}

def build(symbol, setup, bar, levels):
    if setup not in APPROVED: raise ValueError("unsupported V1 setup")
    if not bar.get("closed"): raise ValueError("only completed bars may trigger entries")
    close=float(bar["close"]); high=float(bar["high"]); low=float(bar["low"])
    if setup=="orb":
        trigger=float(levels["opening_range_high"]); invalid=float(levels["opening_range_low"]); confirmed=close>trigger
    elif setup=="20_day_breakout":
        trigger=float(levels["prior_20_day_high"]); invalid=float(levels.get("invalidation",low)); confirmed=close>trigger
    else:
        trigger=max(float(levels["vwap"]),float(levels["ma"])); invalid=min(float(levels["vwap"]),float(levels["ma"]),low); confirmed=close>trigger and float(bar.get("open",close))<=trigger
    return {"symbol":symbol.upper(),"setup":setup,"trigger":trigger,"confirmation":"closed_bar_close_above_trigger","confirmed":confirmed,"entry":close if confirmed else None,"invalidation":invalid,"bar_closed":True}
