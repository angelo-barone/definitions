# Word of the Week

A small widget that shows one word and its definition on an iPhone home screen and on a Windows desktop. Both read the same list, so they always show the same word.

- **Weekly or daily:** in weekly mode (the current setting) the word changes on Sunday.
- **List order:** after the last word, the cycle starts again from the top.
- **New words** go to the end of the list.
- **Light and dark** follow the phone and Windows theme.

## iPhone setup (one time)

1. Install **Scriptable** (free) from the App Store.
2. Open Scriptable, tap **+**, and paste in the contents of [`iphone/WordOfTheDay.js`](iphone/WordOfTheDay.js).
3. Name the script `Word of the Day`, then tap ▶ to check that it works.
4. Long-press the home screen → **+** → **Scriptable** → **Medium** → **Add Widget**.
5. Long-press the widget → **Edit Widget** → set **Script** to `Word of the Day`.

## PC setup (Windows, one time)

1. Install **Rainmeter** (free) from [rainmeter.net](https://www.rainmeter.net).
2. Download [`pc/WordOfTheDay.rmskin`](pc/WordOfTheDay.rmskin), double-click it, then click **Install**.
   This removes Rainmeter's sample widgets and puts the word in the top left of your desktop.

Right-click the widget → **Refresh word list now** to pull new words immediately.
Otherwise it checks every 30 minutes.

## Changing words

Ask Claude, for example "add *laconic*", "remove *sedulous*" or "switch to daily".
Claude makes the change and pushes it live, with no setup needed.

If you'd rather do it yourself, the change lives in one file, [`words.json`](words.json),
and there's a helper script for editing it safely:

```
python3 tools/wordctl.py today
python3 tools/wordctl.py schedule
python3 tools/wordctl.py add laconic --pos adjective --def "Using very few words."
python3 tools/wordctl.py remove laconic
python3 tools/wordctl.py edit laconic --def "New definition."
python3 tools/wordctl.py mode weekly
```

Changes go live as soon as they're on `main`, because both widgets download from there.

## How it was made

Built with Claude (Claude Code). Angelo Barone directs the features and tests it.

## License

MIT. See `LICENSE`.
