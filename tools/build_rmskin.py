#!/usr/bin/env python3
"""Build pc/WordOfTheDay.rmskin, a one-click Rainmeter installer for the PC widget.

An .rmskin is a zip with RMSKIN.ini at its root and skins under Skins/,
followed by a 16-byte footer: zip size (uint64 LE), flags (uint8), b"RMSKIN\\0".
"""

import io
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIN = ROOT / "pc" / "WordOfTheDay"
LAYOUT = ROOT / "pc" / "Layout" / "Rainmeter.ini"
OUT = ROOT / "pc" / "WordOfTheDay.rmskin"

RMSKIN_INI = """[rmskin]
Name=Word of the Day
Author=angelo-barone
Version=1.1
MinimumRainmeter=4.5.0
MinimumWindows=10.0
LoadType=Layout
Load=WordOfTheDay
"""


def crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def main():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("RMSKIN.ini", crlf(RMSKIN_INI))
        for name in ("WordOfTheDay.ini", "WordOfTheDay.lua"):
            z.writestr(f"Skins/WordOfTheDay/{name}", crlf((SKIN / name).read_text(encoding="utf-8")))
        # Loading the layout unloads all other skins and places the widget top left.
        z.writestr("Layouts/WordOfTheDay/Rainmeter.ini", crlf(LAYOUT.read_text(encoding="utf-8")))
    data = buf.getvalue()
    OUT.write_bytes(data + struct.pack("<QB7s", len(data), 0, b"RMSKIN\0"))
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
