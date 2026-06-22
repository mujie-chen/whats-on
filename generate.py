#!/usr/bin/env python3
"""
Build whats-on.ics from events.json.

NO-APPROXIMATION GUARANTEE: an event reaches the .ics only via
  (a) a deterministic calendar rule, or
  (b) an explicit confirmed instance.
Anything in 'pending' or 'feed' is never emitted. If a date isn't known,
the calendar is silent about it - it does not guess.

Stdlib only (no pip install in CI). Python 3.9+.
"""
import json
from datetime import date, timedelta, datetime, timezone

YEARS_AHEAD = 6          # how far to project rule-based events
SRC = "events.json"
OUT = "whats-on.ics"


def nth_weekday(year, month, weekday, n):
    """n-th `weekday` (Mon=0..Sun=6) of month. n=1 -> first."""
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + timedelta(days=offset + 7 * (n - 1))


def first_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 1)


def rule_instances(ev, start_year):
    out = []
    for y in range(start_year, start_year + YEARS_AHEAD):
        r = ev["rule"]
        if r == "fixed":
            s = date(y, ev["month"], ev["day"])
        elif r == "first_weekday":
            s = first_weekday(y, ev["month"], ev["weekday"])
        elif r == "nth_weekday":
            s = nth_weekday(y, ev["month"], ev["weekday"], ev["n"])
        else:
            continue
        out.append((s, ev.get("duration", 1)))
    return out


def esc(t):
    return (t.replace("\\", "\\\\").replace(";", "\\;")
             .replace(",", "\\,").replace("\n", "\\n"))


def fold(line):
    out = []
    while len(line.encode("utf-8")) > 73:
        cut = 73
        while len(line[:cut].encode("utf-8")) > 73:
            cut -= 1
        out.append(line[:cut]); line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)


def vevent(uid, start, days, summary, desc, cat):
    end = start + timedelta(days=days)
    return [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        "DTSTAMP:20260101T000000Z",
        f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
        fold(f"SUMMARY:{esc(summary)}"),
        fold(f"DESCRIPTION:{esc(desc)}"),
        fold(f"CATEGORIES:{esc(cat)}"),
        "TRANSP:TRANSPARENT",
        "END:VEVENT",
    ]


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    today = date.today()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    L = ["BEGIN:VCALENDAR", "VERSION:2.0",
         "PRODID:-//Levi//What's On (confirmed-only)//EN",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:What's On",
         "X-WR-TIMEZONE:Asia/Singapore",
         fold("X-WR-CALDESC:Confirmed dates only - no approximations. Pending"
              " events appear once their real date is known."),
         f"X-GENERATED:{now}"]   # changes every run -> keeps the cron alive

    emitted = 0
    for ev in data.get("rule_events", []):
        for i, (s, days) in enumerate(rule_instances(ev, today.year)):
            if s + timedelta(days=days) < today:
                continue
            L += vevent(f"rule-{abs(hash(ev['name']))%10**8}-{s:%Y%m%d}",
                        s, days, ev["name"], ev.get("note", ""), ev["category"])
            emitted += 1

    for ev in data.get("confirmed_events", []):
        for inst in ev["instances"]:
            s = datetime.strptime(inst["start"], "%Y-%m-%d").date()
            days = inst.get("days", 1)
            if s + timedelta(days=days) < today:
                continue
            L += vevent(f"conf-{abs(hash(ev['name']))%10**8}-{s:%Y%m%d}",
                        s, days, ev["name"], ev.get("note", ""), ev["category"])
            emitted += 1

    L.append("END:VCALENDAR")
    open(OUT, "w", encoding="utf-8").write("\r\n".join(L) + "\r\n")

    pend = len(data.get("pending_events", []))
    feed = len(data.get("feed_events", []))
    print(f"emitted {emitted} confirmed/rule events | "
          f"{pend} pending (no date yet) | {feed} on live feeds")


if __name__ == "__main__":
    main()
