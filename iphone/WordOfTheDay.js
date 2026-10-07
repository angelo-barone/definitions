// Word of the Day: Scriptable widget (medium size).
// Reads words.json from GitHub, so new words show up without touching the phone.

const DATA_URL = "https://raw.githubusercontent.com/angelo-barone/definitions/main/words.json";

// ---- cycle logic (keep in sync with tools/wordctl.py and pc/WordOfTheDay.lua) ----

function dayNumber(y, m, d) {
  // Days since 1970-01-01 for a calendar date (no time zones, no DST).
  return Math.round(Date.UTC(y, m - 1, d) / 86400000);
}

function period(n, mode) {
  // Weekly: 1970-01-01 was a Thursday; +4 puts week boundaries on Sundays.
  return mode === "weekly" ? Math.floor((n + 4) / 7) : n;
}

function currentIndex(data, y, m, d) {
  const [ay, am, ad] = data.anchor.date.split("-").map(Number);
  const elapsed = period(dayNumber(y, m, d), data.mode) - period(dayNumber(ay, am, ad), data.mode);
  const len = data.words.length;
  return (((data.anchor.index + elapsed) % len) + len) % len;
}

function isValid(data) {
  return data && Array.isArray(data.words) && data.words.length > 0 &&
    data.anchor && typeof data.anchor.date === "string" &&
    Number.isInteger(data.anchor.index) && (data.mode === "daily" || data.mode === "weekly");
}

// ---- end cycle logic ----

const fm = FileManager.local();
const cachePath = fm.joinPath(fm.cacheDirectory(), "word-of-the-day.json");

async function loadData() {
  try {
    const req = new Request(DATA_URL);
    req.timeoutInterval = 15;
    const data = await req.loadJSON();
    if (!isValid(data)) throw new Error("invalid words.json");
    fm.writeString(cachePath, JSON.stringify(data));
    return data;
  } catch (e) {
    // Offline or GitHub hiccup: fall back to the last good copy.
    if (fm.fileExists(cachePath)) return JSON.parse(fm.readString(cachePath));
    throw e;
  }
}

const colors = {
  bg: Color.dynamic(new Color("#FFFFFF"), new Color("#1C1C1E")),
  text: Color.dynamic(new Color("#1C1C1E"), new Color("#F2F2F7")),
  muted: Color.dynamic(new Color("#6E6E73"), new Color("#A1A1A6")),
};

function addText(stack, str, font, color, lines) {
  const t = stack.addText(str);
  t.font = font;
  t.textColor = color;
  t.lineLimit = lines;
  t.minimumScaleFactor = 0.7;
  return t;
}

function buildWidget(data) {
  const now = new Date();
  const entry = data.words[currentIndex(data, now.getFullYear(), now.getMonth() + 1, now.getDate())];

  const w = new ListWidget();
  w.backgroundColor = colors.bg;
  w.setPadding(14, 16, 14, 16);

  addText(w, data.mode === "weekly" ? "WORD OF THE WEEK" : "WORD OF THE DAY",
    Font.semiboldSystemFont(11), colors.muted, 1);
  w.addSpacer(4);

  const head = w.addStack();
  head.centerAlignContent();
  addText(head, entry.word, new Font("Georgia-Bold", 26), colors.text, 1);
  head.addSpacer(8);
  addText(head, entry.pos, Font.italicSystemFont(14), colors.muted, 1);
  head.addSpacer();

  w.addSpacer(6);
  addText(w, entry.definition, Font.systemFont(15), colors.text, 4);
  w.addSpacer();

  // Ask iOS to refresh just after local midnight (iOS treats this as a hint).
  const next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 1);
  w.refreshAfterDate = next;
  return w;
}

function errorWidget(message) {
  const w = new ListWidget();
  w.backgroundColor = colors.bg;
  addText(w, "Word of the Day", Font.semiboldSystemFont(13), colors.text, 1);
  w.addSpacer(4);
  addText(w, "Couldn't load words: " + message, Font.systemFont(12), colors.muted, 3);
  w.refreshAfterDate = new Date(Date.now() + 30 * 60 * 1000);
  return w;
}

let widget;
try {
  widget = buildWidget(await loadData());
} catch (e) {
  widget = errorWidget(String(e.message || e));
}

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  await widget.presentMedium();
}
Script.complete();
