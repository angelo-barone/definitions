#!/usr/bin/env python3
"""Manage words.json: the single source of truth for the iPhone and PC widgets.

Both widgets compute the current word from the date alone:

    index = (anchor.index + period(today) - period(anchor.date)) mod len(words)

where period() is a day number (daily mode) or a Sunday-start week number
(weekly mode). Every command that changes the list length or the mode first
re-anchors to "today", so the word currently showing never jumps and nothing
is skipped or repeated.

Usage:
    python3 tools/wordctl.py today
    python3 tools/wordctl.py schedule [--count 14]
    python3 tools/wordctl.py add WORD --pos POS --def "DEFINITION"
    python3 tools/wordctl.py remove WORD
    python3 tools/wordctl.py edit WORD [--pos POS] [--def "DEFINITION"]
    python3 tools/wordctl.py mode daily|weekly
    python3 tools/wordctl.py check
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

WORDS_FILE = Path(__file__).resolve().parent.parent / "words.json"

# The owner's local time zone. Only used to decide what "today" is when
# re-anchoring; the widgets themselves use the device's local date.
TIMEZONE = "America/Toronto"

MODES = ("daily", "weekly")


def day_number(d: dt.date) -> int:
    """Days since 1970-01-01. Must match dayNumber() in the widgets."""
    return (d - dt.date(1970, 1, 1)).days


def period(d: dt.date, mode: str) -> int:
    n = day_number(d)
    if mode == "weekly":
        # 1970-01-01 was a Thursday; +4 shifts week boundaries to Sundays.
        return (n + 4) // 7
    return n


def current_index(data: dict, today: dt.date) -> int:
    anchor_date = dt.date.fromisoformat(data["anchor"]["date"])
    elapsed = period(today, data["mode"]) - period(anchor_date, data["mode"])
    return (data["anchor"]["index"] + elapsed) % len(data["words"])


def today_local() -> dt.date:
    return dt.datetime.now(ZoneInfo(TIMEZONE)).date()


def load() -> dict:
    data = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    validate(data)
    return data


def save(data: dict) -> None:
    validate(data)
    WORDS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(data: dict) -> None:
    if data.get("mode") not in MODES:
        sys.exit(f"invalid mode: {data.get('mode')!r}")
    anchor = data.get("anchor", {})
    dt.date.fromisoformat(anchor.get("date", ""))
    words = data.get("words")
    if not words:
        sys.exit("words list is empty")
    if not isinstance(anchor.get("index"), int) or not 0 <= anchor["index"] < len(words):
        sys.exit(f"anchor.index out of range: {anchor.get('index')!r}")
    seen = set()
    for w in words:
        for key in ("word", "pos", "definition"):
            if not isinstance(w.get(key), str) or not w[key].strip():
                sys.exit(f"entry missing {key!r}: {w}")
        if w["word"].lower() in seen:
            sys.exit(f"duplicate word: {w['word']}")
        seen.add(w["word"].lower())


def reanchor(data: dict, today: dt.date) -> int:
    idx = current_index(data, today)
    data["anchor"] = {"date": today.isoformat(), "index": idx}
    return idx


def find(data: dict, word: str) -> int:
    for i, w in enumerate(data["words"]):
        if w["word"].lower() == word.lower():
            return i
    sys.exit(f"word not found: {word}")


def label(data: dict) -> str:
    return "this week" if data["mode"] == "weekly" else "today"


def cmd_today(data, today, _args):
    i = current_index(data, today)
    w = data["words"][i]
    print(f"{label(data)} ({data['mode']}, {today}): #{i + 1}/{len(data['words'])} "
          f"{w['word']} ({w['pos']}): {w['definition']}")


def cmd_schedule(data, today, args):
    step = 7 if data["mode"] == "weekly" else 1
    if step == 7:
        today -= dt.timedelta(days=(today.weekday() + 1) % 7)  # back to Sunday
    for k in range(args.count):
        d = today + dt.timedelta(days=k * step)
        print(f"{d}  {data['words'][current_index(data, d)]['word']}")


def cmd_add(data, today, args):
    if any(w["word"].lower() == args.word.lower() for w in data["words"]):
        sys.exit(f"already in list: {args.word}")
    reanchor(data, today)
    data["words"].append({"word": args.word, "pos": args.pos, "definition": args.definition})
    save(data)
    print(f"added {args.word} at #{len(data['words'])}")


def cmd_remove(data, today, args):
    if len(data["words"]) == 1:
        sys.exit("cannot remove the last word")
    r = find(data, args.word)
    idx = reanchor(data, today)
    del data["words"][r]
    if r < idx:
        idx -= 1
    # If the current word was removed, the following word takes its place today.
    data["anchor"]["index"] = idx % len(data["words"])
    save(data)
    print(f"removed {args.word}")


def cmd_edit(data, _today, args):
    w = data["words"][find(data, args.word)]
    if args.pos:
        w["pos"] = args.pos
    if args.definition:
        w["definition"] = args.definition
    save(data)
    print(f"edited {w['word']}")


def cmd_mode(data, today, args):
    if data["mode"] == args.mode:
        print(f"already {args.mode}")
        return
    reanchor(data, today)
    data["mode"] = args.mode
    save(data)
    print(f"mode set to {args.mode}")


def cmd_check(data, today, _args):
    print(f"ok: {len(data['words'])} words, mode {data['mode']}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--date", type=dt.date.fromisoformat, help="pretend today is this date (YYYY-MM-DD)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("today")
    s = sub.add_parser("schedule")
    s.add_argument("--count", type=int, default=14)
    a = sub.add_parser("add")
    a.add_argument("word")
    a.add_argument("--pos", required=True)
    a.add_argument("--def", dest="definition", required=True)
    r = sub.add_parser("remove")
    r.add_argument("word")
    e = sub.add_parser("edit")
    e.add_argument("word")
    e.add_argument("--pos")
    e.add_argument("--def", dest="definition")
    m = sub.add_parser("mode")
    m.add_argument("mode", choices=MODES)
    sub.add_parser("check")
    args = p.parse_args()

    data = load()
    today = args.date or today_local()
    globals()[f"cmd_{args.cmd}"](data, today, args)


if __name__ == "__main__":
    main()
