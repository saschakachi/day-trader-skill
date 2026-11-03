#!/usr/bin/env python3
"""Historical evidence, not prediction: summarize out-of-sample trade outcomes in R."""
import math, statistics

def summarize(rows):
    rs=[float(x["r"]) for x in rows if x.get("r") is not None]
    n=len(rs)
    if not n:return {"sample_size":0,"status":"insufficient_evidence"}
    wins=sum(r>0 for r in rs); mean=statistics.fmean(rs); med=statistics.median(rs)
    sd=statistics.stdev(rs) if n>1 else 0.0; se=sd/math.sqrt(n) if n else 0
    return {"sample_size":n,"win_rate":wins/n,"avg_r":round(mean,4),"median_r":round(med,4),"confidence_interval_95_avg_r":[round(mean-1.96*se,4),round(mean+1.96*se,4)],"avg_mae_r":round(statistics.fmean(float(x.get("mae_r",0)) for x in rows),4),"avg_mfe_r":round(statistics.fmean(float(x.get("mfe_r",0)) for x in rows),4),"target_first":sum(x.get("outcome")=="target_first" for x in rows),"stop_first":sum(x.get("outcome")=="stop_first" for x in rows),"neither":sum(x.get("outcome")=="neither" for x in rows),"status":"historical_evidence_only"}
