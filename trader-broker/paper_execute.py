#!/usr/bin/env python3
"""V1 execution boundary: records simulated orders and can never call a live broker."""
import argparse, datetime, hashlib, json, os, uuid


def fingerprint(ticket):
    payload=json.dumps(ticket,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def validate_config(config):
    if config.get("mode") != "paper" or config.get("paper") is not True:
        raise ValueError("paper mode required")
    if config.get("live_trading_enabled") is not False:
        raise ValueError("live trading must be disabled")
    if config.get("risk_gate_bypass") is not False:
        raise ValueError("risk gate bypass must be disabled")


def execute(ticket, risk, approved, path="trader/paper_orders.json", config=None):
    config = config or {"mode":"paper","paper":True,"live_trading_enabled":False,"risk_gate_bypass":False}
    validate_config(config)
    if risk.get("verdict") != "PASS" or risk.get("paper_only") is not True:
        raise ValueError("risk gate did not PASS for paper execution")
    expected=fingerprint(ticket)
    if risk.get("ticket_fingerprint") != expected:
        raise ValueError("risk result does not match exact ticket")
    if approved is not True: raise ValueError("explicit user approval required")
    order={"paper_order_id":"paper-"+uuid.uuid4().hex[:12],"mode":"paper","status":"simulated","created_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"ticket_fingerprint":expected,"ticket":ticket,"risk":risk}
    data=[]
    if os.path.exists(path):
        with open(path,encoding="utf-8") as f: data=json.load(f)
        if not isinstance(data,list): raise ValueError("paper order store must be a JSON array")
    data.append(order)
    directory=os.path.dirname(path)
    if directory: os.makedirs(directory,exist_ok=True)
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,indent=2)
    return order


def main():
    p=argparse.ArgumentParser(); p.add_argument("--ticket",required=True); p.add_argument("--risk",required=True); p.add_argument("--config",default="trader/config.json"); p.add_argument("--approve",action="store_true"); p.add_argument("--out",default="trader/paper_orders.json"); a=p.parse_args()
    with open(a.ticket,encoding="utf-8") as f:t=json.load(f)
    with open(a.risk,encoding="utf-8") as f:r=json.load(f)
    with open(a.config,encoding="utf-8") as f:c=json.load(f)
    print(json.dumps(execute(t,r,a.approve,a.out,c),indent=2))
if __name__=="__main__": main()
