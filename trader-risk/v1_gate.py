#!/usr/bin/env python3
"""Fail-closed V1 risk overlay. Paper trading only."""
import argparse, datetime, hashlib, json, os
# Python 3.8-compatible US Eastern DST conversion for aware timestamps.
def eastern_time(instant):
    utc = instant.astimezone(datetime.timezone.utc)
    year = utc.year
    spring = nth_weekday(year, 3, 6, 2)
    autumn = nth_weekday(year, 11, 6, 1)
    start = datetime.datetime(year, 3, spring.day, 7, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(year, 11, autumn.day, 6, tzinfo=datetime.timezone.utc)
    hours = -4 if start <= utc < end else -5
    return utc.astimezone(datetime.timezone(datetime.timedelta(hours=hours)))


def nth_weekday(year, month, weekday, nth):
    first = datetime.date(year, month, 1)
    return first + datetime.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (nth - 1))

def last_weekday(year, month, weekday):
    if month == 12:
        last = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    return last - datetime.timedelta(days=(last.weekday() - weekday) % 7)

def observed(date):
    if date.weekday() == 5:
        return date - datetime.timedelta(days=1)
    if date.weekday() == 6:
        return date + datetime.timedelta(days=1)
    return date

def easter(year):
    a = year % 19; b = year // 100; c = year % 100
    d = b // 4; e = b % 4; f = (b + 8) // 25
    g = (b - f + 1) // 3; h = (19*a + b - d - g + 15) % 30
    i = c // 4; k = c % 4; l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1
    return datetime.date(year, month, day)

def market_closed(day):
    y = day.year
    holidays = set()
    for yr in (y - 1, y, y + 1):
        holidays.update((observed(datetime.date(yr, 1, 1)),
                         observed(datetime.date(yr, 6, 19)),
                         observed(datetime.date(yr, 7, 4)),
                         observed(datetime.date(yr, 12, 25))))
    holidays.update((nth_weekday(y, 1, 0, 3), nth_weekday(y, 2, 0, 3),
                     easter(y) - datetime.timedelta(days=2),
                     last_weekday(y, 5, 0), nth_weekday(y, 9, 0, 1),
                     nth_weekday(y, 11, 3, 4)))
    return day.weekday() >= 5 or day in holidays

def early_close(day):
    thanksgiving = nth_weekday(day.year, 11, 3, 4)
    return day == thanksgiving + datetime.timedelta(days=1) or (day.month == 12 and day.day == 24) or (day.month == 7 and day.day == 3)



def load(path, default=None):
    if not os.path.exists(path): return default
    with open(path, encoding="utf-8") as f: return json.load(f)


def fingerprint(ticket):
    payload=json.dumps(ticket,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def evaluate(ticket, config, stats=None, now=None):
    stats = stats or {}
    reasons = []
    if config.get("mode") != "paper" or config.get("paper") is not True or config.get("live_trading_enabled") is not False:
        reasons.append("V1 requires paper mode; live trading must be disabled")
    if config.get("risk_gate_bypass") is not False:
        reasons.append("risk gate bypass must be explicitly disabled")
    if config.get("allow_short") is not False or config.get("allow_margin") is not False or config.get("allow_options") is not False:
        reasons.append("shorts, margin and options must be disabled")
    if str(ticket.get("side", "buy")).lower() != "buy": reasons.append("V1 is long-only")
    setup = ticket.get("setup") or (ticket.get("plan") or {}).get("setup")
    if setup not in config.get("setups", []): reasons.append("setup is not approved for V1")
    if config.get("closed_bars_only") is not True or ticket.get("bar_closed") is not True: reasons.append("trigger bar is not confirmed closed")
    entry, stop, target = [ticket.get(k) for k in ("entry", "stop", "target")]
    try:
        entry, stop, target = float(entry), float(stop), float(target)
        if not stop < entry < target: reasons.append("long trade requires stop < entry < target")
        risk = entry - stop
        rr = (target-entry)/risk if risk > 0 else 0
        if rr < float(config.get("min_reward_risk", 1.5)): reasons.append("reward:risk below minimum")
        qty = int(ticket.get("position_size") or ticket.get("qty") or 0)
        if qty <= 0: reasons.append("position size must be positive")
        if qty * risk > float(config.get("max_loss_per_trade_usd", 125)) + 1e-9: reasons.append("planned loss exceeds per-trade limit")
        equity = float(config.get("account_equity_usd", 25000))
        if qty * entry > equity * float(config.get("max_position_pct", 20))/100 + 1e-9: reasons.append("position exceeds account percentage cap")
    except (TypeError, ValueError): reasons.append("entry, stop and target must be numeric")
    if float(stats.get("daily_loss_usd", 0)) >= float(config.get("max_daily_loss_usd", 375)): reasons.append("daily loss kill switch active")
    weekly_cap = float(config.get("account_equity_usd",25000))*float(config.get("max_weekly_loss_pct",4))/100
    if float(stats.get("weekly_loss_usd",0)) >= weekly_cap: reasons.append("weekly loss kill switch active")
    if int(stats.get("trades_today",0)) >= int(config.get("max_trades_per_day",4)): reasons.append("daily trade limit reached")
    if int(stats.get("consecutive_losses",0)) >= int(config.get("max_consecutive_losses",3)): reasons.append("consecutive-loss kill switch active")
    if stats.get("kill_switch"): reasons.append("manual kill switch active")
    if stats.get("cooldown_active"): reasons.append("cooldown active")
    # Naive injected test times are interpreted as New York wall clock.
    # Production uses timezone-aware UTC converted to New York, including DST.
    now = now if now is not None else datetime.datetime.now(datetime.timezone.utc)
    if now.tzinfo is not None:
        now = eastern_time(now)
    day = now.date()
    if day.weekday() >= 5: reasons.append("market closed on weekends")
    elif market_closed(day): reasons.append("NYSE closed on this date")
    hhmm = now.strftime("%H:%M")
    cutoff = min(config.get("no_entries_after", "15:30"), "12:30") if early_close(day) else config.get("no_entries_after", "15:30")
    if hhmm < config.get("no_entries_before","09:35") or hhmm > cutoff: reasons.append("outside entry window")
    return {"verdict":"BLOCK" if reasons else "PASS", "reasons":reasons, "paper_only":True, "ticket_fingerprint":fingerprint(ticket)}


def main():
    p=argparse.ArgumentParser(); p.add_argument("--ticket",required=True); p.add_argument("--config",default="trader/config.json"); p.add_argument("--stats",default="trader/state/session.json"); p.add_argument("--now")
    a=p.parse_args(); ticket=load(a.ticket,{}); config=load(a.config,{}) ; stats=load(a.stats,{}) or {}
    now=datetime.datetime.fromisoformat(a.now) if a.now else None
    out=evaluate(ticket,config,stats,now); print(json.dumps(out,indent=2)); raise SystemExit(0 if out["verdict"]=="PASS" else 1)
if __name__=="__main__": main()
