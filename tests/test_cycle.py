#!/usr/bin/env python3
"""Cross-checks the cycle math in wordctl.py, the iPhone script and the PC Lua script.

Run: python3 tests/test_cycle.py   (needs node and lua5.1 on PATH)
"""

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import wordctl  # noqa: E402

JS = ROOT / "iphone" / "WordOfTheDay.js"
LUA = ROOT / "pc" / "WordOfTheDay" / "WordOfTheDay.lua"

CASES = [
    {"mode": m, "anchor": {"date": a, "index": i}, "words": [{"word": f"w{k}", "pos": "n", "definition": "d"} for k in range(n)]}
    for m in ("daily", "weekly")
    for a, i, n in (("2026-10-07", 0, 3), ("2026-10-04", 2, 5), ("2027-03-14", 1, 7), ("2024-02-29", 0, 1))
]
START = dt.date(2025, 12, 20)
DATES = [START + dt.timedelta(days=k) for k in range(0, 900, 1)]


def expected():
    return [[wordctl.current_index(c, d) for d in DATES] for c in CASES]


def js_results():
    src = JS.read_text()
    logic = src[src.index("// ---- cycle logic"):src.index("// ---- end cycle logic")]
    prog = logic + f"""
const cases = {json.dumps(CASES)};
const dates = {json.dumps([[d.year, d.month, d.day] for d in DATES])};
console.log(JSON.stringify(cases.map(c => {{ if (!isValid(c)) throw new Error('invalid'); return dates.map(([y, m, d]) => currentIndex(c, y, m, d)); }})));
"""
    return json.loads(subprocess.run(["node", "-e", prog], capture_output=True, text=True, check=True).stdout)


def lua_results():
    out = []
    for c in CASES:
        dates = ",".join(f"{{{d.year},{d.month},{d.day}}}" for d in DATES)
        prog = f"""
dofile([[{LUA}]])
local data = JsonDecode([==[{json.dumps(c, ensure_ascii=False)}]==])
assert(IsValid(data), 'invalid')
local out = {{}}
for _, d in ipairs({{{dates}}}) do out[#out + 1] = CurrentIndex(data, d[1], d[2], d[3]) end
print(table.concat(out, ','))
"""
        res = subprocess.run(["lua5.1", "-e", prog], capture_output=True, text=True, check=True).stdout.strip()
        out.append([int(x) for x in res.split(",")])
    return out


def lua_json_roundtrip():
    real = (ROOT / "words.json").read_text(encoding="utf-8")
    tricky = json.dumps({"s": "café — \"q\" \\ / \n \U0001F600", "n": [-1.5e2, 0, True, False, None]})
    prog = f"""
dofile([[{LUA}]])
local d = JsonDecode([==[{real}]==])
assert(IsValid(d))
print(#d.words, d.words[1].word, d.mode, d.anchor.index)
local t = JsonDecode([==[{tricky}]==])
io.write(t.s)
print('|' .. t.n[1] .. ',' .. t.n[2] .. ',' .. tostring(t.n[3]) .. ',' .. tostring(t.n[4]))
"""
    return subprocess.run(["lua5.1", "-e", prog], capture_output=True, text=True, check=True).stdout


def main():
    exp = expected()
    assert js_results() == exp, "JS cycle math differs from wordctl.py"
    assert lua_results() == exp, "Lua cycle math differs from wordctl.py"

    # Weekly mode must change word exactly on Sundays.
    weekly = CASES[4]
    for prev, d in zip(DATES, DATES[1:]):
        changed = wordctl.current_index(weekly, prev) != wordctl.current_index(weekly, d)
        assert changed == (d.weekday() == 6), f"weekly change on {d}"

    real = json.loads((ROOT / "words.json").read_text(encoding="utf-8"))
    out = lua_json_roundtrip()
    first = real["words"][0]["word"]
    assert out.startswith(f"{len(real['words'])}\t{first}\t{real['mode']}\t{real['anchor']['index']}"), out
    assert "café — \"q\" \\ / \n \U0001F600|-150,0,true,false" in out, out
    print(f"ok: {len(CASES)} cases x {len(DATES)} days match across Python, JS and Lua")



def test_edits():
    """add/remove/mode never change today's word, and add keeps the order intact."""
    import argparse
    import copy
    import tempfile

    tmp = Path(tempfile.mkdtemp()) / "words.json"
    wordctl.WORDS_FILE = tmp
    base = {"mode": "daily", "anchor": {"date": "2026-10-07", "index": 0},
            "words": [{"word": f"w{k}", "pos": "n", "definition": "d"} for k in range(4)]}

    for mode in ("daily", "weekly"):
        for offset in range(0, 30):
            today = dt.date(2026, 10, 7) + dt.timedelta(days=offset)
            start = copy.deepcopy(base)
            start["mode"] = mode
            before = start["words"][wordctl.current_index(start, today)]["word"]

            d = copy.deepcopy(start)
            wordctl.cmd_add(d, today, argparse.Namespace(word="new", pos="n", definition="d"))
            assert d["words"][wordctl.current_index(d, today)]["word"] == before
            # Walk forward: every word appears once before any repeats, new word last.
            step = 7 if mode == "weekly" else 1
            seq = [d["words"][wordctl.current_index(d, today + dt.timedelta(days=k * step))]["word"] for k in range(5)]
            assert sorted(seq) == sorted(w["word"] for w in d["words"]), seq
            assert seq[(4 - int(before[1:])) % 5] == "new", seq

            d = copy.deepcopy(start)
            wordctl.cmd_remove(d, today, argparse.Namespace(word="w0" if before != "w0" else "w1"))
            assert d["words"][wordctl.current_index(d, today)]["word"] == before

            d = copy.deepcopy(start)
            wordctl.cmd_mode(d, today, argparse.Namespace(mode="weekly" if mode == "daily" else "daily"))
            assert d["words"][wordctl.current_index(d, today)]["word"] == before
    print("ok: add/remove/mode keep the current word and the order")


if __name__ == "__main__":
    main()
    test_edits()
