# Word of the Day widgets

`words.json` is the single source of truth. The iPhone widget (Scriptable, `iphone/`) and the PC widget (Rainmeter, `pc/`) both download it from the `main` branch on GitHub.

## Changing the word list

- Always use `tools/wordctl.py` (add / remove / edit / mode). Never hand-edit `words.json`, because the tool re-anchors the cycle so today's word never jumps.
- New words go at the end of the list (the owner's preference).
- Definitions: when the owner gives one, use it verbatim. Otherwise write a short, clear dictionary-style definition (one sentence, about 15 words or fewer, so it fits a medium iPhone widget). Always include the part of speech.
- After a change, run `python3 tests/test_cycle.py` and `python3 tools/wordctl.py today`.
- The owner allows pushing word-list changes directly to main. Code changes go through a PR.

## Code changes

- The cycle math lives in three places and must stay identical: `tools/wordctl.py`, `iphone/WordOfTheDay.js` and `pc/WordOfTheDay/WordOfTheDay.lua`. `tests/test_cycle.py` cross-checks them (it needs `node` and `lua5.1`).
- After editing anything in `pc/WordOfTheDay/`, rebuild the installer with `python3 tools/build_rmskin.py`.
