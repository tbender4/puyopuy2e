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
`puyopuy2e-saturn-rcN.bps` (N: the release candidate number) and a patcher for convenience.

### Linux/macOS
```sh
./patch.sh "PUYO_PUYO_TSU____ (Track 1).bin" puyopuy2e-saturn-rcN.bps
```

### Windows
```powershell
powershell -ExecutionPolicy Bypass -File .\patch.ps1 "PUYO_PUYO_TSU____ (Track 1).bin" puyopuy2e-saturn-rcN.bps
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
output Track 1 instead of copying 606 MB.

## What is translated

### Shared with the arcade and Mega Drive versions
- title logo
- the 12 attract tutorial pages
- gameplay HUD (`CHAIN`, `OFFSET`, `K.O.`, `YAY!`)
- the tower (`PICK YOUR RIVAL`, Nomi's `I'M HERE`, `YAY!`, `HOORAY!` and `OUCH!`), `CONTINUE?`, `PAUSE`,
- 2P rule select (`CHOOSE A RULE!`)
- mode select (`CHOOSE A MODE!`, with the Saturn-only fourth mode, `ENDLESS PUYO`)
- options romaji (`RULE SET`, `OFFSET`).

### Saturn only
- The 1P difficulty cards and their descriptions (`PRACTICE`, `NORMAL`, `TSUU`)
- Save file select (`NEW GAME` slots), delete data, and the backup RAM and controller
  messages
- Rule Edit menu, the rule editor (all settings and the nuisance hardness labels) and the
  rule slot save and load boxes
- Tsuu mode character select (`START!`) and Nomi on the BEST RECORDS screen
- The sound test's two bonus video titles
- The ending staff roll: roles and every name as [MobyGames](https://www.mobygames.com/game/13047/puyo-puyo-2/credits/sega-saturn/)
  credits them

#### Cutscenes (Game Arts files, Milestone D)
- The Act Against AIDS card (`COURAGE AND LOVE` and its three lines)
- Nomi's signs (`I'M HERE`, `I SAID I'M HERE!`, `SHOULD BE HERE`, `FOUND IT!`, `MAYBE I'M HERE`)
- Cockadoodle's two captions, and `THIRTY MINUTES / LATER` for `30分経過`
- Shezo's ヘンタイ / タイヘン signs keep the Japanese (the swap is the joke) with `PERVERT` /
  `TERRIBLE` above them
- The other signs and sound effects keep the Japanese with a small English word: `GULP!` (Draco), `MA`, `MAS`, `MASK`, `MASKED`
  (Masked Satan spelling マスクド), `ROCK` (Mini Zombie), `DONK!` (Nasu Grave), `UNBEATEN` and `GUTS!` (Lycanthrope),
  `WAAAH!` (Rulue), `HERE TOO.` (Zombie)
- English subtitles for the voice lines of all 74 skits (Normal and Tsuu mode). `STORY DEMO` on OPTIONS page 2 has new options: 
    - `SUBTITLES`: at the bottom (default),
    - `SPEAKER`: next to whoever speaks
    - `SIGNS ONLY`: only translated signs, no voice subtitles.
    - `OFF`: no skits

Translations are from Domino054's [translated cutscene videos](https://youtu.be/aKZwf3sSVWM). Thank you for graciously permitting use of the translation!

## Not translated

- Sound-effect lettering in the skits (ざく, どかーん, グサッ, ガ〜ン, うわーん) keeps the Japanese art

The voice audio (subtitled, see above) and the FMV videos are left as they are.

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
| Options page 2: `STORY DEMO` | ![](screenshots/saturn/options2_jp.png) | ![](screenshots/saturn/options2_en.png) |
| Skit subtitles: `SUBTITLES` | ![](screenshots/saturn/skit_jp.png) | ![](screenshots/saturn/skit_subtitles_en.png) |
| Skit subtitles: `SPEAKER` | ![](screenshots/saturn/skit_jp.png) | ![](screenshots/saturn/skit_speaker_en.png) |
| Tutorial | ![](screenshots/saturn/tutorial_jp.png) | ![](screenshots/saturn/tutorial_en.png) |
| Tutorial | ![](screenshots/saturn/tutorial2_jp.png) | ![](screenshots/saturn/tutorial2_en.png) |
| Staff roll | ![](screenshots/saturn/credits_jp.png) | ![](screenshots/saturn/credits_en.png) |
