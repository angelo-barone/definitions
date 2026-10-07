# definitions

A word-of-the-day widget for the iPhone home screen and the Windows desktop.
Both widgets read [`words.json`](words.json), so they always show the same word.

- **Daily or weekly:** in weekly mode the word changes on Sunday.
- **List order:** after the last word, the cycle starts again from the top.
- **New words** go to the end of the list.
- **Light/dark** follows your phone and Windows theme.

## iPhone setup (one time)

1. Install **Scriptable** (free) from the App Store.
2. Open Scriptable, tap **+**, and paste in the contents of [`iphone/WordOfTheDay.js`](iphone/WordOfTheDay.js).
3. Name the script `Word of the Day`, then tap ▶ to check that it works.
4. Long-press the home screen → **+** → **Scriptable** → **Medium** → **Add Widget**.
5. Long-press the widget → **Edit Widget** → set **Script** to `Word of the Day`.

## PC setup (Windows, one time)

1. Install **Rainmeter** (free) from [rainmeter.net](https://www.rainmeter.net).
2. Download [`pc/WordOfTheDay.rmskin`](pc/WordOfTheDay.rmskin) and double-click it, then click **Install**.
3. Drag the widget to where you want it. To keep it there, right-click it → **Settings** → **Position** → **On desktop**.

Right-click the widget → **Refresh word list now** to pull new words immediately.
Otherwise it checks every 30 minutes.

## Changing words

Ask Claude, e.g. "add *laconic*", "remove *sedulous*", "switch to weekly".
Under the hood that runs [`tools/wordctl.py`](tools/wordctl.py):

```
python3 tools/wordctl.py today
python3 tools/wordctl.py schedule
python3 tools/wordctl.py add laconic --pos adjective --def "Using very few words."
python3 tools/wordctl.py remove laconic
python3 tools/wordctl.py edit laconic --def "New definition."
python3 tools/wordctl.py mode weekly
```

Changes go live once they're on `main`. The widgets download from there.
