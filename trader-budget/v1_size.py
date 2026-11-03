#!/usr/bin/env python3
"""Stop-first V1 position sizing."""
import argparse, json, math

def size(entry, stop, equity=25000, risk_usd=125, max_position_pct=20, cash=None):
    entry=float(entry); stop=float(stop); equity=float(equity); risk_usd=float(risk_usd)
    if stop >= entry: raise ValueError("long V1 requires stop below entry")
    risk_per_share=entry-stop
    by_risk=math.floor(risk_usd/risk_per_share)
    by_position=math.floor((equity*float(max_position_pct)/100)/entry)
    by_cash=math.floor(float(cash)/entry) if cash is not None else by_position
    qty=max(0,min(by_risk,by_position,by_cash))
    return {"qty":qty,"risk_per_share":round(risk_per_share,4),"planned_risk_usd":round(qty*risk_per_share,2),"position_value_usd":round(qty*entry,2),"binding_limit":min((by_risk,"risk"),(by_position,"position"),(by_cash,"cash"))[1]}

def main():
    p=argparse.ArgumentParser(); p.add_argument("entry",type=float); p.add_argument("stop",type=float); p.add_argument("--equity",type=float,default=25000); p.add_argument("--risk",type=float,default=125); p.add_argument("--max-position-pct",type=float,default=20); p.add_argument("--cash",type=float)
    a=p.parse_args(); print(json.dumps(size(a.entry,a.stop,a.equity,a.risk,a.max_position_pct,a.cash),indent=2))
if __name__=="__main__": main()
