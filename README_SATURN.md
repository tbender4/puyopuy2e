# Puyo Puyo 2: Sega Saturn English Translation

Port of `puyopuy2e` to the Sega Saturn release **Puyo Puyo Tsuu** (`T-6601G`, V1.200).
Besides everything shared with the arcade and [Mega Drive](README_MD.md) versions, the
Saturn menus, cards and dialogs, which exist only on this disc, are redrawn in English.

![the title in BizHawk](screenshots/saturn/title_en.png)
![the 1P difficulty cards](screenshots/saturn/difficulty_en.png)

## Base disc

A raw `.bin`/`.cue` dump with two tracks; only Track 1 is changed:

| File | Size | CRC32 |
|---|---|---|
| `PUYO_PUYO_TSU____ (Track 1).bin` | 606,498,480 | `3f966f9d` |
| `PUYO_PUYO_TSU____ (Track 2).bin` | 1,764,000 | |

## Patch

Each [release](https://github.com/tbender4/puyopuy2e/releases) has
`puyopuy2e-saturn-no-red-puyos.bps` and a patcher for convenience.

#### Linux/macOS
```sh
./patch.sh "PUYO_PUYO_TSU____ (Track 1).bin" puyopuy2e-saturn-no-red-puyos.bps
```

#### Windows
```powershell
powershell -ExecutionPolicy Bypass -File .\patch.ps1 "PUYO_PUYO_TSU____ (Track 1).bin" puyopuy2e-saturn-no-red-puyos.bps
```

Both write `Puyo Puyo 2 (English) (Track 1).bin` and `Puyo Puyo 2 (English).cue` next to
the original.

A BPS-capable patcher works as well.

## Build From Source

A Python script is available:

```sh
python3 make_puyopuy2e_saturn.py ["PUYO_PUYO_TSU____ (Track 1).bin" | FOLDER] [OUT_DIR]
```

The default input is `saturn/` (the `.cue` and Track 2 must sit next to Track 1) and the
default output `dist/saturn/`. `--logo` picks the title logo as for the other versions
(`no-red-puyos` default, `with-red-puyos`, `original`); `--fast` overlays onto an existing
output Track 1 instead of copying 606 MB. Every translated file is written back in place
inside its original disc sectors, so the image keeps its size and layout.

## What is translated

#### Shared with the arcade and Mega Drive versions
- title logo
- the 12 attract tutorial pages
- gameplay HUD (`CHAIN`, `OFFSET`, `K.O.`, `YAY!`)
- the tower (`PICK YOUR RIVAL`, Nomi's `I'M HERE`, `YAY!`, `HOORAY!` and `OUCH!`), `CONTINUE?`, `PAUSE`,
- 2P rule select (`CHOOSE A RULE!`)
- mode select (`CHOOSE A MODE!`, with the Saturn-only fourth mode, `ENDLESS PUYO`)
- options romaji (`RULE SET`, `OFFSET`).

#### Saturn only
- The 1P difficulty cards and their descriptions (`PRACTICE`, `NORMAL`, `TSUU`)
- Save file select (`NEW GAME` slots), delete data, and the backup RAM and controller
  messages
- Rule Edit menu, the rule editor (all settings and the nuisance hardness labels) and the
  rule slot save and load boxes
- Tsuu mode character select (`START!`) and Nomi on the BEST RECORDS screen
- The sound test's two bonus video titles
- The ending staff roll: roles and every name as [MobyGames](https://www.mobygames.com/game/13047/puyo-puyo-2/credits/sega-saturn/)
  credits them (credited aliases kept as aliases)

## Not translated yet

These are Game Arts' own files, in other formats, planned as Milestone D:

- The voiced manzai skits between matches (their captions and sound-effect lettering)
- The `30分経過` ("30 minutes later") caption
- The Saturn Act Against AIDS card in attract mode

The voice audio and the FMV videos are left as they are.

## Screenshots

| | Original | English |
|---|---|---|
| Title | ![](screenshots/saturn/title_jp.png) | ![](screenshots/saturn/title_en.png) |
| Mode select | ![](screenshots/saturn/mode_jp.png) | ![](screenshots/saturn/mode_en.png) |
| 1P difficulty: Normal | ![](screenshots/saturn/difficulty_jp.png) | ![](screenshots/saturn/difficulty_en.png) |
| 1P difficulty: Practice | ![](screenshots/saturn/practice_jp.png) | ![](screenshots/saturn/practice_en.png) |
| 1P difficulty: Tsuu | ![](screenshots/saturn/tsuu_jp.png) | ![](screenshots/saturn/tsuu_en.png) |
| Save file select | ![](screenshots/saturn/save_jp.png) | ![](screenshots/saturn/save_en.png) |
| Tsuu character select | ![](screenshots/saturn/charsel_jp.png) | ![](screenshots/saturn/charsel_en.png) |
| Tower | ![](screenshots/saturn/tower_jp.png) | ![](screenshots/saturn/tower_en.png) |
| Match won | ![](screenshots/saturn/yay_jp.png) | ![](screenshots/saturn/yay_en.png) |
| Continue | ![](screenshots/saturn/continue_jp.png) | ![](screenshots/saturn/continue_en.png) |
| 2P rule select | ![](screenshots/saturn/rules_jp.png) | ![](screenshots/saturn/rules_en.png) |
| Rule Edit menu | ![](screenshots/saturn/ruleedit_jp.png) | ![](screenshots/saturn/ruleedit_en.png) |
| Rule editor | ![](screenshots/saturn/editor_jp.png) | ![](screenshots/saturn/editor_en.png) |
| Rule save | ![](screenshots/saturn/savebox_jp.png) | ![](screenshots/saturn/savebox_en.png) |
| Options | ![](screenshots/saturn/options_jp.png) | ![](screenshots/saturn/options_en.png) |
| Tutorial | ![](screenshots/saturn/tutorial_jp.png) | ![](screenshots/saturn/tutorial_en.png) |
| Tutorial | ![](screenshots/saturn/tutorial2_jp.png) | ![](screenshots/saturn/tutorial2_en.png) |
| Staff roll | ![](screenshots/saturn/credits_jp.png) | ![](screenshots/saturn/credits_en.png) |
