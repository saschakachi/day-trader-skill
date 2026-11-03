#!/usr/bin/env python3
"""V1 execution boundary: records simulated orders and can never call a live broker."""
import argparse, datetime, json, os, uuid

def execute(ticket, risk, approved, path="trader/paper_orders.json"):
    if risk.get("verdict") != "PASS": raise ValueError("risk gate did not PASS")
    if approved is not True: raise ValueError("explicit user approval required")
    order={"paper_order_id":"paper-"+uuid.uuid4().hex[:12],"mode":"paper","status":"simulated","created_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"ticket":ticket,"risk":risk}
    data=[]
    if os.path.exists(path):
        with open(path,encoding="utf-8") as f: data=json.load(f)
    data.append(order); os.makedirs(os.path.dirname(path),exist_ok=True)
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,indent=2)
    return order

def main():
    p=argparse.ArgumentParser(); p.add_argument("--ticket",required=True); p.add_argument("--risk",required=True); p.add_argument("--approve",action="store_true"); p.add_argument("--out",default="trader/paper_orders.json"); a=p.parse_args()
    with open(a.ticket,encoding="utf-8") as f:t=json.load(f)
    with open(a.risk,encoding="utf-8") as f:r=json.load(f)
    print(json.dumps(execute(t,r,a.approve,a.out),indent=2))
if __name__=="__main__": main()
